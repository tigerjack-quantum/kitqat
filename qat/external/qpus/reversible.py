"""For now it is only a test bench, creating a fake Program object.
 Virtually, it should be integrated into qat, taking a circuit as input and running the simulation.
"""
from __future__ import annotations

import logging
import operator
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Sequence, Set, Union

from qat.lang.AQASM.gates import PredefGate
from qat.lang.AQASM.gates import Gate
if TYPE_CHECKING:
    from qat.lang.AQASM.program import Program

from bitarray import bitarray

logger = logging.getLogger(__name__)


class RGate(Enum):
    NOT = auto()
    SWAP = auto()


class RProgram():

    rev_gate_names = ('X', 'NOT', 'SWAP')

    def __init__(self):
        self._ops = [
        ]  # should contain the list of operations for logging purposes
        self.qbits: bitarray = bitarray()

    def qalloc(self, n=1):
        self.qbits.extend('0' * n)

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
    def _get_and_apply_gate(cls, rprogram: RProgram, gate: Gate,
                            qbits: Sequence[int]):
        if not gate.name.endswith(cls.rev_gate_names):
            raise AttributeError(
                "Reversible gates are only NOT (X), SWAP and their controlled versions"
            )
        if gate.name == 'SWAP':
            ctrls = set(qbits[:-2])
            trgts = set(qbits[-2:])
            rgate = RGate.SWAP
        elif gate.name == 'X':
            if len(qbits) == 2:
                gate.name = 'CNOT'
                return cls._get_and_apply_gate(rprogram, gate, qbits)
            elif len(qbits) == 3:
                gate.name = 'CCNOT'
                return cls._get_and_apply_gate(rprogram, gate, qbits)
            elif len(qbits) == 1:
                rgate = RGate.NOT
                trgts = {qbits[-1]}
                ctrls = set()
        elif gate.name == 'CNOT':
            ctrls = {qbits[0]}
            trgts = {qbits[1]}
            rgate = RGate.NOT
        elif gate.name == 'CCNOT':
            ctrls = {qbits[0], qbits[1]}
            trgts = {qbits[2]}
            rgate = RGate.NOT
        else:
            raise Exception(
                f"Got an unknown gate that passed the first check {gate.name}")

        rprogram.apply(rgate, ctrls, trgts)

    @classmethod
    def program_to_rprogram(cls, qprogram: Program) -> RProgram:
        rprogram = RProgram()
        rprogram.qalloc(qprogram.qbit_count)
        for op in qprogram.op_list:
            qbits = [qb.index for qb in op.qbits]
            if isinstance(op.gate, PredefGate):
                cls._get_and_apply_gate(rprogram, op.gate, qbits)
            elif op.gate.subgate is not None and isinstance(
                    op.gate.subgate, PredefGate):
                cls._get_and_apply_gate(rprogram, op.gate.subgate, qbits)
        return rprogram
