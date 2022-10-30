"""For now it is only a test bench, creating a fake Program object. Virtually,
 it should be integrated into qat, taking a circuit as input and running the
 simulation.

"""
from __future__ import annotations

import logging
import operator
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Sequence, Set, Union

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit

from bitarray import bitarray, util

logger = logging.getLogger(__name__)


class RGate(Enum):
    NOT = auto()
    SWAP = auto()


class RProgram():

    rev_gate_names = ('X', 'NOT', 'SWAP')

    def __init__(self):
        self.ops = [
        ]  # should contain the list of operations for logging purposes
        self.qbits: bitarray = bitarray()
        self.rregs: dict[range, str] = {}

    def qalloc(self, n=1, name=None):
        rang = range(len(self.qbits),
                     len(self.qbits) + n)  # upper not included
        if name is None:
            name = str(rang)[6:].replace(', ', '_').replace(')', '')
        elif name in self.rregs:
            raise ValueError("Already another register with the same name")
        self.rregs[rang] = name
        self.qbits.extend(util.zeros(n))

    def apply(self, gate: RGate, ctrls: Optional[Set[int]],
              trgts: Union[int, Set[int]]):
        if self.qbits is None:
            raise AttributeError("You should initialize your qubits")

        # print(ctrls)
        # if ctrls is not None:
        #     print(len(ctrls))

        ctrl = (ctrls is None or len(ctrls) == 0) or (
            len(ctrls) == 1 and operator.itemgetter(*ctrls)(self.qbits)
            == 1) or (len(ctrls) > 1
                      and all(operator.itemgetter(*ctrls)(self.qbits)))
        if not ctrl:
            return

        if isinstance(trgts, int):
            trgts = {trgts}
        if ctrls is not None and not ctrls.isdisjoint(trgts):
            raise ValueError("The target and control set should be disjoint")
        self.ops.append((gate, ctrls, trgts))
        if gate == RGate.NOT:
            for trgt in trgts:
                self.qbits.invert(trgt)
        elif gate == RGate.SWAP:
            if len(trgts) == 2:
                _trgts = list(trgts)
                self.qbits[_trgts[1]], self.qbits[_trgts[0]] = self.qbits[
                    _trgts[0]], self.qbits[_trgts[1]]
            else:
                raise ValueError("Swap gates can have only 2 targets")
        else:
            raise ValueError(f"Unknown gate {gate}")

    @classmethod
    def _get_and_apply_gate(cls, qcircuit: 'Circuit', rprogram: RProgram,
                            gate: str, qbits: Sequence[int]):
        if not gate.endswith(cls.rev_gate_names):
            if gate.startswith('_'):
                return cls._get_and_apply_gate(qcircuit, rprogram,
                                               qcircuit.gateDic[gate].subgate,
                                               qbits)
            else:
                raise AttributeError(
                    "Reversible gates: X, SWAP and their controlled versions")
        if gate == 'SWAP':
            ctrls = set(qbits[:-2])
            trgts = set(qbits[-2:])
            rgate = RGate.SWAP
        elif gate == 'X':
            if len(qbits) == 2:
                return cls._get_and_apply_gate(qcircuit, rprogram, 'CNOT',
                                               qbits)
            elif len(qbits) == 3:
                return cls._get_and_apply_gate(qcircuit, rprogram, 'CCNOT',
                                               qbits)
            else:
                rgate = RGate.NOT
                trgts = {qbits[-1]}
                ctrls = set(qbits[:-1])
        elif gate == 'CNOT' or gate == 'C-NOT':
            ctrls = {qbits[0]}
            trgts = {qbits[1]}
            rgate = RGate.NOT
        elif gate == 'CCNOT' or gate == 'C-C-NOT':
            ctrls = {qbits[0], qbits[1]}
            trgts = {qbits[2]}
            rgate = RGate.NOT
        else:
            raise Exception(
                f"Got an unknown gate that passed the first check {gate}")

        rprogram.apply(rgate, ctrls, trgts)

    def get_result(self) -> bitarray:
        return self.qbits

    def get_result_by_name(self):
        res = {}
        for rang, name in self.rregs.items():
            res[name] = self.qbits[rang.start:rang.stop]
        return res

    @classmethod
    def circuit_to_rprogram(
        cls, qcirc: Circuit, reg_names: dict[range, str] = dict()) -> RProgram:
        """Warn: circuit should be generated with inline=True to avoid errors"""
        rprogram = RProgram()
        for qr in qcirc.qregs:
            rang = range(qr.start, qr.start + qr.length)
            name = reg_names.get(rang, None)
            rprogram.qalloc(qr.length, name)
        for op in qcirc.ops:
            cls._get_and_apply_gate(qcirc, rprogram, op.gate, op.qbits)

        return rprogram
