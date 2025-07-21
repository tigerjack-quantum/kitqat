import functools
import operator
from typing import TYPE_CHECKING, Dict, List, NamedTuple, Type, Union

from qat.lang.AQASM.qbool import QBoolArray
from qat.lang.AQASM.qint import QInt
from qatext.qroutines.fake import fake_gate

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit
    from qat.lang.AQASM.bits import Qbit, QRegister
    from qat.lang.AQASM.program import Program


class QRegsProperties(NamedTuple):
    # This is for 1 or more collection of qregs
    slic: slice
    # number of qregs aggregated
    n: int | None
    # size of each qreg
    m: int | None
    qtype: Type[Union[bool, int, str]]
    # if True, should set the slice stop to -1, and n to -1, and m to -1
    unknown_size: bool = False


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


def add_name_to_qbits_following_pattern(program: "Program",
                                        pattern: Dict[str, List["Qbit"]]):
    """It allows to add a fake gate to a set of qbit in order to help their
    visualization."""
    for k, qbits in pattern.items():
        for i, qbit in enumerate(qbits):
            absgate = fake_gate(f"{k}_{i}", 1)
            program.apply(absgate, qbit)


def qregs_array_alloc(
    pr: "Program",
    n: int,
    size: int,
    name: str,
    qtype: Type[Union[bool, int, str]],
    qregs_properties: dict[str, QRegsProperties],
):
    """Register allocation logic for an array of `n` quantum registers, each
    cell composed of `size` qubits. The array will be associated to the given
    `name`. The variable `qtype` can be equal to `bool`, `int` or `str`, and it
    is used both to specify the myqlm type of the quantum register, and in
    quantum state related functions in order to interpret the qubits as ints,
    booleans or directly print them as bitstrings.

    """
    regs = []
    if qtype == int:
        qtype_myqlm = QInt
    elif qtype == bool:
        qtype_myqlm = QBoolArray
    else:
        qtype_myqlm = None
    for _ in range(n):
        qr = pr.qalloc(size, qtype_myqlm)
        regs.append(qr)
    key = f"{name}"
    start = regs[0].start
    stop = regs[-1].start + size
    qregs_properties[key] = QRegsProperties(slice(start, stop), n, size, qtype)
    return regs


def qregs_array_noalloc(n: int | None,
                        size: int | None,
                        name: str,
                        start_idx: int,
                        qtype,
                        qregs_properties: dict[str, QRegsProperties],
                        unknown_size=False):
    """Register declaration, without allocation, for a register of `n`
    elements, each cell having `size` qubits. Since there is no allocation, you
    should specify the qubit index `start_idx` from which this array starts.
    This function can be also used to allocate ancillary qubits of unknown
    length (such as the ones automatically generated inside QRoutine) by
    setting `unknown_size=True`.

    The variable `qtype` can be equal to `bool`, `int` or `str`, and it is used
    in quantum state related functions in order to interpret the qubits as
    ints, booleans or directly print them as bitstrings.

    """
    key = f"{name}"
    start = start_idx
    if size is None:
        unknown_size = True
        n = None

    if unknown_size:
        stop = None
    else:
        stop = start_idx + size * n  # type: ignore
    qregs_properties[key] = QRegsProperties(slice(start, stop), n, size, qtype,
                                            unknown_size)
