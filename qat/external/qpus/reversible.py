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
        self.rbits: bitarray = bitarray()
        self.rregs: dict[range, str] = {}

    def qalloc(self, n=1, name=None):
        rang = range(len(self.rbits),
                     len(self.rbits) + n)  # upper not included
        if name is None:
            name = str(rang)[6:].replace(', ', '_').replace(')', '')
        elif name in self.rregs:
            raise ValueError("Already another register with the same name")
        self.rregs[rang] = name
        self.rbits.extend(util.zeros(n))

    def apply(self, gate: RGate, ctrls: Optional[Set[int]],
              trgts: Union[int, Set[int]]):
        if self.rbits is None:
            raise AttributeError("You should initialize your qubits")

        # print(ctrls)
        # if ctrls is not None:
        #     print(len(ctrls))

        ctrl = (ctrls is None or len(ctrls) == 0) or (
            len(ctrls) == 1 and operator.itemgetter(*ctrls)(self.rbits)
            == 1) or (len(ctrls) > 1
                      and all(operator.itemgetter(*ctrls)(self.rbits)))
        if not ctrl:
            return

        if isinstance(trgts, int):
            trgts = {trgts}
        if ctrls is not None and not ctrls.isdisjoint(trgts):
            raise ValueError("The target and control set should be disjoint")
        self.ops.append((gate, ctrls, trgts))
        if gate == RGate.NOT:
            for trgt in trgts:
                self.rbits.invert(trgt)
        elif gate == RGate.SWAP:
            if len(trgts) == 2:
                _trgts = list(trgts)
                self.rbits[_trgts[1]], self.rbits[_trgts[0]] = self.rbits[
                    _trgts[0]], self.rbits[_trgts[1]]
            else:
                raise ValueError("Swap gates can have only 2 targets")
        else:
            raise ValueError(f"Unknown gate {gate}")

    @classmethod
    def _get_and_apply_gate(cls, qcircuit: 'Circuit', rprogram: RProgram,
                            gate: str, rbits: Sequence[int]):
        if not gate.endswith(cls.rev_gate_names):
            if gate.startswith('_'):
                return cls._get_and_apply_gate(qcircuit, rprogram,
                                               qcircuit.gateDic[gate].subgate,
                                               rbits)
            else:
                raise AttributeError(
                    "Reversible gates: X, SWAP and their controlled versions")
        if gate == 'SWAP':
            ctrls = set(rbits[:-2])
            trgts = set(rbits[-2:])
            rgate = RGate.SWAP
        elif gate == 'X':
            if len(rbits) == 2:
                return cls._get_and_apply_gate(qcircuit, rprogram, 'CNOT',
                                               rbits)
            elif len(rbits) == 3:
                return cls._get_and_apply_gate(qcircuit, rprogram, 'CCNOT',
                                               rbits)
            else:
                rgate = RGate.NOT
                trgts = {rbits[-1]}
                ctrls = set(rbits[:-1])
        elif gate == 'CNOT' or gate == 'C-NOT':
            ctrls = {rbits[0]}
            trgts = {rbits[1]}
            rgate = RGate.NOT
        elif gate == 'CCNOT' or gate == 'C-C-NOT':
            ctrls = {rbits[0], rbits[1]}
            trgts = {rbits[2]}
            rgate = RGate.NOT
        else:
            raise Exception(
                f"Got an unknown gate that passed the first check {gate}")

        rprogram.apply(rgate, ctrls, trgts)

    def get_result(self) -> bitarray:
        return self.rbits

    def get_result_by_name(self):
        res = {}
        for rang, name in self.rregs.items():
            res[name] = self.rbits[rang.start:rang.stop]
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
