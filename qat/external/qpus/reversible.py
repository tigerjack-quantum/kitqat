"""For now it is only a test bench, creating a fake Program object. Virtually,
 it should be integrated into qat, taking a circuit as input and running the
 simulation.

"""
from __future__ import annotations

import logging
import operator
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Sequence

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit
    from qat.lang.AQASM.routines import QRoutine

from bitarray import bitarray, util

logger = logging.getLogger(__name__)


class RGate(Enum):
    """Reversible Gate: NOT, SWAP or RESET"""
    NOT = auto()
    SWAP = auto()
    RESET = auto()


class RProgram():
    """A Reversible equivalent of the qat Program object. Differently from it,
    when you call the apply function, the reversible gate is immediately
    applied onto the reversible bit.
    """

    rev_gate_names = ('X', 'NOT', 'SWAP')

    def __init__(self):
        self.ops = [
        ]  # should contain the list of operations for logging purposes
        self.rbits: bitarray = bitarray()
        self.rregs: dict[str, range] = {}

    def ralloc(self, n=1, name: Optional[str] = None):
        """Allocate a register of `n` reversible bits. `n` defaults to 1. You
        can additionally decide to name this register passing the `name`
        parameter.

        """
        rang = range(len(self.rbits),
                     len(self.rbits) + n)  # upper not included
        if name is None:
            name = str(rang)[6:].replace(', ', '_').replace(')', '')
        elif name in self.rregs:
            raise ValueError("Already another register with the same name")
        self.rregs[name] = rang
        self.rbits.extend(util.zeros(n))

    def apply(self, gate: RGate, *rbits: int):
        """Apply a Reversible gate on the reversible bits. Last bits are the
        targets, first the controls (if any)."""
        if self.rbits is None:
            raise AttributeError("You should initialize your qubits")
        if gate == RGate.NOT:
            ntrgts = 1
        elif gate == RGate.SWAP:
            ntrgts = 2
        elif gate == RGate.RESET:
            ntrgts = 1
        else:
            raise ValueError(f"Unknown gate {gate}")
        trgts = rbits[-1:-1 * ntrgts - 1:-1]
        ctrls = rbits[:len(rbits) - ntrgts]
        # arity = len(rbits) - ntrgts
        if len(trgts) + len(ctrls) != len(rbits):
            raise ValueError(f"Wrong number of rbits {len(rbits)}")
        if ctrls is not None and not set(ctrls).isdisjoint(set(trgts)):
            raise ValueError("The target and control set should be disjoint")
        ctrl = (ctrls is None or len(ctrls) == 0) or (
            len(ctrls) == 1 and operator.itemgetter(*ctrls)(self.rbits)
            == 1) or (len(ctrls) > 1
                      and all(operator.itemgetter(*ctrls)(self.rbits)))
        self.ops.append((gate, *ctrls, *trgts))
        if not ctrl:
            # Nothing to do here
            return

        if gate == RGate.NOT:
            for trgt in trgts:
                self.rbits.invert(trgt)
        elif gate == RGate.SWAP:
            self.rbits[trgts[1]], self.rbits[trgts[0]] = self.rbits[
                trgts[0]], self.rbits[trgts[1]]
        elif gate == RGate.RESET:
            self.rbits[trgts[0]] = 0
        else:
            raise ValueError(f"Unknown gate {gate}")

    def _apply_gate_from_name(self, gatename: str, rbits: Sequence[int]):
        """Apply a gate given the gatename. Allowed SWAP, X, NOT, CNOT, C-NOT, CX, C-X, CCNOT, C-C-NOT, C-C-X, CCX"""

        if gatename == 'SWAP':
            ctrls = set(rbits[:-2])
            trgts = set(rbits[-2:])
            rgate = RGate.SWAP
        elif gatename == 'X' or gatename == 'NOT':
            if len(rbits) == 2:
                return self._apply_gate_from_name('CNOT', rbits)
            elif len(rbits) == 3:
                return self._apply_gate_from_name('CCNOT', rbits)
            else:
                rgate = RGate.NOT
                trgts = {rbits[-1]}
                ctrls = set(rbits[:-1])
        elif gatename in ('CNOT', 'C-NOT', 'C-X', 'CX'):
            ctrls = {rbits[0]}
            trgts = {rbits[1]}
            rgate = RGate.NOT
        elif gatename in ('CCNOT', 'C-C-NOT', 'C-C-X', 'CCX'):
            ctrls = {rbits[0], rbits[1]}
            trgts = {rbits[2]}
            rgate = RGate.NOT
        else:
            raise AttributeError(
                f"Got an unknown gate that passed the first check {gatename}")

        self.apply(rgate, *ctrls, *trgts)

    def get_result(self) -> bitarray:
        return self.rbits

    def get_result_by_name(self):
        res = {}
        for name, rang in self.rregs.items():
            res[name] = self.rbits[rang.start:rang.stop]
        return res

    def filter_result_by_name(self, *name: str):
        res = {}
        for _name, rang  in self.rregs.items():
            if _name in name:
                res[_name] = self.rbits[rang.start:rang.stop]
        return res

    @classmethod
    def circuit_to_rprogram(
        cls, qcirc: Circuit, reg_names: dict[str, range] = dict()) -> RProgram:
        """Convert a qat Circuit object to a reversible program :class:`~qat.external.qpus.reversible.RProgram`, applying all the operations contained.
        """
        rprogram = RProgram()
        reg_names_inv = dict((v,k) for k, v in reg_names.items())
        for qr in qcirc.qregs:
            rang = range(qr.start, qr.start + qr.length)
            name = reg_names_inv.get(rang, None)
            rprogram.ralloc(qr.length, name)
        qdiff = qcirc.nbqbits - len(rprogram.rbits)
        if qdiff > 0:
            # there are ancillae automatically generated from subroutines
            rprogram.ralloc(qdiff, "auto_ancillae")

        rprogram.apply_gates_from_circuit(qcirc, qcirc)
        return rprogram

    def apply_gates_from_circuit(
        self,
        top_circ: 'Circuit',
        operation_circ: 'Circuit',
    ):
        """Apply all the gates from the circuit `operation_circ` given. While
        `operation_circ` is the circuit containing the gates to be applied,
        `top_circ` is the top level circuit in which the `operation_circ` is
        embedded. `operation_circ` can indeed be a circuit implementation of a
        gate embedded in the `top_circ`.

        If you want to apply all the gates from the top_circ, you can set the two to the same value.

        """
        # It's iterating on the inlined version
        for op in operation_circ:
            gatename = op.gate
            if gatename is None:
                if op.type == 1:
                    # measure operation, NOP
                    continue
                elif op.type == 2:
                    # reset
                    self.apply(RGate.RESET, op.qbits)
            subcirc = top_circ.gateDic[gatename].circuit_implementation
            if subcirc is not None:
                # subcirc can be applied to a different subset of qubits
                self.apply_gates_from_circuit(top_circ, subcirc)
            else:
                if not gatename.endswith(self.rev_gate_names):
                    if gatename.startswith('_'):
                        # Should be a custom gate with defined subgate
                        gatename = top_circ.gateDic[gatename].subgate
                    else:
                        raise AttributeError(
                            "Reversible gates accepted: X, SWAP and their controlled versions"
                        )
                self._apply_gate_from_name(gatename, op.qbits)

    def apply_gates_from_qroutine(
        self,
        qroutine: 'QRoutine',
        qbits: Sequence[int] = [],
    ):
        """Warn: this work with QRoutine, not with QRoutine lifted to
        AbstractGate through the @build_gate annotation. If you have such a
        gate and you to access the underlying QRoutine, use the tilde operator.
        Indeed, the QRoutine is easier since all the gates are inlined.

        """
        if len(qbits) == 0:
            qbits = range(qroutine.arity)
        elif len(qbits) < qroutine.arity:
            raise Exception(f"Too few qbits {len(qbits)}")
        qrout_to_orig: dict[int, int] = {
            a: b
            for (a, b) in zip(range(qroutine.arity), qbits)
        }
        for op in qroutine.op_list:
            op_qbits = [qrout_to_orig[i] for i in op.args]
            gatename = op.gate.name
            if gatename is not None:
                self._apply_gate_from_name(gatename, op_qbits)
                continue
            if op.gate.subgate is not None:
                gatename = op.gate.subgate.name
                if gatename is not None:
                    self._apply_gate_from_name(gatename, op_qbits)
                    continue

            self.apply_gates_from_qroutine(op.gate, op_qbits)
