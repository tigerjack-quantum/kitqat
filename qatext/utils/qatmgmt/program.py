from typing import TYPE_CHECKING, Dict, List, NamedTuple, Type, Union

from qat.lang.AQASM.qbool import QBoolArray
from qat.lang.AQASM.qint import QInt
# from qatext.utils.qatmgmt.qbits import QRegsProperties
from qatext.qroutines.fake import fake_gate

if TYPE_CHECKING:
    from qat.lang.AQASM.bits import Qbit, QRegister


class QRegsProperties(NamedTuple):
    # This is for 1 or more collection of qregs
    slic: slice
    # number of qregs aggregated
    n: int | None
    # size of each qreg
    m: int | None
    # list of qregs
    qregs: list['QRegister'] | None
    qtype: Type[Union[bool, int, str]]
    # if True, should set the slice stop to -1, and n to -1, and m to -1
    unknown_size: bool = False


class ProgramWrapper:

    def __init__(self, program_instance):
        self._program = program_instance
        self._qregnames_to_properties: dict[str, QRegsProperties] = {}

    def __getattr__(self, name):
        return getattr(self._program, name)

    def add_name_to_qbits_following_pattern(self, pattern: Dict[str,
                                                                List["Qbit"]]):
        """It allows to add a fake gate to a set of qbit in order to help their
        visualization."""
        for k, qbits in pattern.items():
            for i, qbit in enumerate(qbits):
                absgate = fake_gate(f"{k}_{i}", 1)
                self._program.apply(absgate, qbit)

    def qregs_array_alloc(
        self,
        n: int,
        size: int,
        name: str,
        qtype: Type[Union[bool, int, str]],
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
            qr = self._program.qalloc(size, qtype_myqlm)
            regs.append(qr)
        key = f"{name}"
        start = regs[0].start
        stop = regs[-1].start + size
        self._qregnames_to_properties[key] = QRegsProperties(
            slice(start, stop), n, size, regs, qtype)
        return regs

    def qregs_array_noalloc(self,
                            n: int | None,
                            size: int | None,
                            name: str,
                            start_idx: int,
                            qtype,
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
        self._qregnames_to_properties[key] = QRegsProperties(
            slice(start, stop), n, size, None, qtype, unknown_size)
