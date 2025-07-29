# TODO subclass RProgram from ProgramWrapper and override methods
"""For now it is only a test bench, creating a fake Program object.

Virtually, it should be integrated into qat, taking a circuit as input
and running the simulation.
"""
from __future__ import annotations

import logging
import operator
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Sequence

from qatext.utils.bits.conversion import get_ints_from_bitarray
from qatext.utils.qatmgmt.program import ProgramWrapper, QRegsProperties
from qatext.utils.qatmgmt.routines import QRoutineWrapper

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit
    from qat.lang.AQASM.routines import QRoutine
    from qat.lang.AQASM.program import Program

from bitarray import bitarray, util

LOGGER = logging.getLogger(__name__)


class RGate(Enum):
    """Reversible Gate: NOT, SWAP or RESET."""

    NOT = auto()
    SWAP = auto()
    RESET = auto()
    I = auto()


class RProgram:
    """A Reversible equivalent of the qat Program object.

    Differently from it, when you call the apply function, the
    reversible gate is immediately applied onto the reversible bit.
    """

    rev_gate_names = ("X", "NOT", "SWAP", "I")

    def __init__(self):
        self.ops = [
        ]  # should contain the list of operations for logging purposes
        self.rbits: bitarray = bitarray()
        self.rregs: dict[str, QRegsProperties] = {}

    def ralloc(self, n=1, name: Optional[str] = None):
        """Allocate a register of `n` reversible bits.

        `n` defaults to 1. You can additionally decide to name this
        register passing the `name` parameter.
        """
        slic = slice(len(self.rbits),
                     len(self.rbits) + n)  # upper not included
        if name is None:
            name = str(slic)[6:].replace(", ", "_").replace(")", "")
        elif name in self.rregs:
            raise ValueError("Already another register with the same name")
        # TODO once changed to ProgramWrapper subclass, replace None w/ proper
        # register
        qreg_property = QRegsProperties(slic, 1, n, None, str)
        self.rregs[name] = qreg_property
        self.rbits.extend(util.zeros(n))

    def apply(self, gate: RGate, *rbits: int):
        """Apply a Reversible gate on the reversible bits.

        Last bits are the targets, first the controls (if any).
        """
        if self.rbits is None:
            raise AttributeError("You should initialize your qubits")
        if gate == RGate.NOT:
            ntrgts = 1
        elif gate == RGate.SWAP:
            ntrgts = 2
        elif gate == RGate.RESET:
            ntrgts = 1
        elif gate == RGate.I:
            ntrgts = 1
        trgts = rbits[-1:-1 * ntrgts - 1:-1]
        ctrls = rbits[:len(rbits) - ntrgts]
        # arity = len(rbits) - ntrgts
        if len(trgts) + len(ctrls) != len(rbits):
            raise ValueError(f"Wrong number of rbits {len(rbits)}")
        if ctrls is not None and not set(ctrls).isdisjoint(set(trgts)):
            raise ValueError("The target and control set should be disjoint")
        ctrl = ((ctrls is None or len(ctrls) == 0)
                or (len(ctrls) == 1
                    and operator.itemgetter(*ctrls)(self.rbits) == 1)
                or (len(ctrls) > 1
                    and all(operator.itemgetter(*ctrls)(self.rbits))))
        self.ops.append((gate, *ctrls, *trgts))
        if not ctrl:
            # Nothing to do here
            return

        if gate == RGate.NOT:
            for trgt in trgts:
                self.rbits.invert(trgt)
        elif gate == RGate.SWAP:
            self.rbits[trgts[1]], self.rbits[trgts[0]] = (
                self.rbits[trgts[0]],
                self.rbits[trgts[1]],
            )
        elif gate == RGate.RESET:
            self.rbits[trgts[0]] = 0
        elif gate == RGate.I:
            pass

    def _apply_gate_from_name(self, gatename: str, rbits: Sequence[int]):
        """Apply a gate given the gatename.

        Allowed SWAP, X, NOT, CNOT, C-NOT, CX, C-X, CCNOT, C-C-NOT,
        C-C-X, CCX
        """

        if gatename == "SWAP":
            ctrls = set(rbits[:-2])
            trgts = set(rbits[-2:])
            rgate = RGate.SWAP
        elif gatename == "I":
            rgate = RGate.I
            trgts = {rbits[-1]}
            ctrls = set(rbits[:-1])
        elif gatename in (
                "X",
                "NOT",
                "CNOT",
                "C-NOT",
                "C-X",
                "CX",
                "C-C-NOT",
                "CCNOT",
                "C-CNOT",
                "C-C-X",
                "CCX",
        ):
            rgate = RGate.NOT
            trgts = {rbits[-1]}
            ctrls = set(rbits[:-1])
        else:
            raise AttributeError(
                f"Got an unknown gate that passed the first check {gatename}")

        self.apply(rgate, *ctrls, *trgts)

    def get_result(self) -> str:
        return self.rbits.to01()

    def get_result_by_name(self):
        res = {}
        for name, qreg_property in self.rregs.items():
            res[name] = self.rbits[qreg_property.slic]
        return res

    def filter_result_by_name(self, *name: str):
        res = {}
        for _name, qreg_property in self.rregs.items():
            if _name in name:
                res[_name] = self.rbits[qreg_property.slic]
        return res

    @classmethod
    def circuit_to_rprogram(
        cls,
        qcirc: Circuit,
        qregs_properties: dict[str, QRegsProperties] = dict()
    ) -> RProgram:
        """Convert a qat Circuit object to a reversible program
        :class:`~qatext.qpus.reversible.RProgram`, applying all the
        operations contained."""
        rprogram = RProgram()
        # qreg_names_inv = dict((v, k) for k, v in reg_names.items())
        qreg_slices_to_names: dict[slice, str] = {}
        for name, qreg_properties in qregs_properties.items():
            qreg_slices_to_names[qreg_properties.slic] = name
        for qr in qcirc.qregs:
            slic = slice(qr.start, qr.start + qr.length)
            name = qreg_slices_to_names.get(slic, None)
            rprogram.ralloc(qr.length, name)
        qdiff = qcirc.nbqbits - len(rprogram.rbits)
        if qdiff > 0:
            # there are ancillae automatically generated from subroutines
            rprogram.ralloc(qdiff, "auto_ancillae")

        rprogram.apply_gates_from_circuit(qcirc, qcirc)
        return rprogram

    def apply_gates_from_circuit(
        self,
        top_circ: "Circuit",
        operation_circ: "Circuit",
    ):
        """Apply all the gates from the circuit `operation_circ` given. While
        `operation_circ` is the circuit containing the gates to be applied,
        `top_circ` is the top level circuit in which the `operation_circ` is
        embedded. `operation_circ` can indeed be a circuit implementation of a
        gate embedded in the `top_circ`.

        If you want to apply all the gates from the top_circ, you can
        set the two to the same value.
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
                    if gatename.startswith("_"):
                        # Should be a custom gate with defined subgate
                        gatename = top_circ.gateDic[gatename].subgate
                    else:
                        raise AttributeError(
                            "Reversible gates accepted: X, SWAP and their controlled"
                            f" versions, got {gatename}")
                self._apply_gate_from_name(gatename, op.qbits)

    def apply_gates_from_qroutine(
        self,
        qroutine: "QRoutine",
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


@staticmethod
def get_state_from_program(
    pr,
    link: Optional[list],
) -> str:
    circ = pr.to_circ(link=link, inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    res = rpr.get_result()
    return res


@staticmethod
def get_states_from_program(
    pr,
    reg_names_to_properties: dict[str, QRegsProperties],
    # reg_names_to_sizes,
    link: Optional[list],
) -> dict[str, list[int]]:
    circ = pr.to_circ(link=link, inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr.rregs = reg_names_to_properties
    res = rpr.get_result_by_name()
    return res


@staticmethod
def get_states_from_circuit(
    circ,
    reg_names_to_properties: dict[str, QRegsProperties],
) -> dict[str, list[int]]:
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr.rregs = reg_names_to_properties
    res = rpr.get_result_by_name()
    return res


@staticmethod
def get_states_from_program_wrapper(
    prw: ProgramWrapper,
    link: Optional[list],
) -> dict[str, list[int]]:
    circ = prw.to_circ(link=link, inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr.rregs = prw._qregnames_to_properties
    res = rpr.get_result_by_name()
    return res


@staticmethod
def get_states_from_qroutine_wrapper(
    qroutw: QRoutineWrapper,
    link: Optional[list],
) -> dict[str, list[int]]:

    circ = qroutw.to_circ(link=link, inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr.rregs = qroutw._qregnames_to_properties
    states = rpr.get_result_by_name()
    return states


@staticmethod
def get_rprogram_regs(pr: "Program", reg_name_to_slice, link: list):
    res = get_states_from_program(pr, reg_name_to_slice, link=link)
    return res


@staticmethod
def get_rprogram_regs_values_from_states(
    states,
    qregs_properties: dict[str, QRegsProperties],
):
    dic = {}
    for k, v in states.items():
        LOGGER.debug(f"%s: %s", k, v)
        qreg_properties = qregs_properties[k]
        LOGGER.debug("qreg_properties %s", qreg_properties)
        if qreg_properties.unknown_size:
            val = v
        elif qreg_properties.qtype == str:
            val = v
        elif qreg_properties.qtype == bool:
            val = v
        elif qreg_properties.qtype == int:
            assert qreg_properties.n is not None
            assert qreg_properties.m is not None
            val = get_ints_from_bitarray(v, qreg_properties.n,
                                         qreg_properties.m, False)
        else:
            raise Exception("Unknown qtype %s" % qreg_properties.qtype)
        dic[k] = val
    return dic


@staticmethod
def inspect_state_reversible_program(prw: ProgramWrapper, link):
    # this is the get_states_from_program function, but I need circ
    circ = prw.to_circ(link=link, inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr_bits = rpr.rbits
    rpr.rregs = prw._qregnames_to_properties
    state = rpr.get_result_by_name()
    st = "\n"
    st += f"n qbits {circ.nbqbits}\n"
    st += f"n rbits {len(rpr.rbits)}\n"
    # st += f"state obtained {rpr_bits}"
    st += f"state obtained {' ' * 25}->\t{rpr_bits}\n"

    for key, value in get_rprogram_regs_values_from_states(
            state, prw._qregnames_to_properties).items():
        slic = prw._qregnames_to_properties[key].slic
        st += f"{key:<20} [{slic}] ->\t{value}\n"

    return st


@staticmethod
def inspect_state_reversible_qroutine(qroutw: QRoutineWrapper, link):
    # this is the get_states_from_program function, but I need circ
    circ = qroutw.to_circ(link=link, inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr_bits = rpr.rbits
    rpr.rregs = qroutw._qregnames_to_properties
    state = rpr.get_result_by_name()
    st = "\n"
    st += f"n qbits {circ.nbqbits}\n"
    st += f"n rbits {len(rpr.rbits)}\n"
    # st += f"state obtained {rpr_bits}"
    st += f"state obtained {' ' * 25}->\t{rpr_bits}\n"

    for key, value in get_rprogram_regs_values_from_states(
            state, qroutw._qregnames_to_properties).items():
        slic = qroutw._qregnames_to_properties[key].slic
        st += f"{key:<20} [{slic}] ->\t{value}\n"

    return st
