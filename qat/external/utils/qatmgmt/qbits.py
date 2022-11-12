import functools
import operator
from typing import TYPE_CHECKING, Dict, List

from qat.external.utils.qroutines.fake import fake_gate

if TYPE_CHECKING:
    from qat.lang.AQASM import Circuit, Program
    from qat.lang.AQASM.bits import Qbit, QRegister

def get_qbits_to_int_mapping_from_qregs(
        qregs: List['QRegister']) -> Dict[int, 'Qbit']:
    qregs_flat_dict = {
        qbit: qbit.index
        for qbit in functools.reduce(operator.concat,
                                     map(operator.attrgetter('qbits'), qregs))
    }
    return qregs_flat_dict


def get_int_to_qbits_mapping_from_qregs(qregs: List['QRegister']):
    qregs_flat_dict = {
        qbit.index: qbit
        for qbit in functools.reduce(operator.concat,
                                     map(operator.attrgetter('qbits'), qregs))
    }
    return qregs_flat_dict


def get_qbits_from_circuit_idxs(circuit: 'Circuit', *idxs: int):
    mapping = get_int_to_qbits_mapping_from_qregs(circuit.qregs)
    return [mapping[idx] for idx in idxs]


def get_qbits_from_program_idxs(program: 'Program', *idxs: int):
    mapping = get_int_to_qbits_mapping_from_qregs(program.registers)
    return [mapping[idx] for idx in idxs]


def add_name_to_qbits_following_pattern(program: 'Program',
                                        pattern: Dict[str, List['Qbit']]):
    """It allows to add a fake gate to a set of qbit in order to help their
    visualization."""
    for k, qbits in pattern.items():
        for i, qbit in enumerate(qbits):
            absgate = fake_gate(f"{k}_{i}", 1)
            program.apply(absgate, qbit)
