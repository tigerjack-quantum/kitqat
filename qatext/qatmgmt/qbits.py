import functools
import operator
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit
    from qat.lang.AQASM.bits import Qbit, QRegister
    from qat.lang.AQASM.program import Program



def get_qbits_to_int_mapping_from_qregs(
        qregs: List["QRegister"]) -> Dict[int, "Qbit"]:
    qregs_flat_dict = {
        qbit: qbit.index
        for qbit in functools.reduce(operator.concat,
                                     map(operator.attrgetter("qbits"), qregs))
    }
    return qregs_flat_dict


def get_int_to_qbits_mapping_from_qregs(qregs: List["QRegister"]):
    qregs_flat_dict = {
        qbit.index: qbit
        for qbit in functools.reduce(operator.concat,
                                     map(operator.attrgetter("qbits"), qregs))
    }
    return qregs_flat_dict


def get_qbits_from_circuit_idxs(circuit: "Circuit", *idxs: int):
    mapping = get_int_to_qbits_mapping_from_qregs(circuit.qregs)
    return [mapping[idx] for idx in idxs]


def get_qbits_from_program_idxs(program: "Program", *idxs: int):
    mapping = get_int_to_qbits_mapping_from_qregs(program.registers)
    return [mapping[idx] for idx in idxs]
