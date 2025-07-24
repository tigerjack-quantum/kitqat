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

    def qarray_alloc(
        self,
        n: int,
        size: int,
        name: str,
        qtype: Type[Union[bool, int, str]],
    ):
        """Allocates a quantum register array consisting of `n` elements, each
        composed of `size` qubits.

        The array will be associated with the specified `name`. The `qtype`
        parameter defines both the internal type used by MyQLM for the register
        and how the register is interpreted in quantum state inspection
        functions. It can be one of:
        - `bool`: interpret each element as a boolean value;
        - `int`: interpret each element as an integer;
        - `str`: represent each element as a bitstring.

        Parameters:
            n (int): Number of elements in the register array.
            size (int): Number of qubits per element.
            name (str): Name associated with the register.
            qtype (type): Interpretation type (`bool`, `int`, or `str`).

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

    def qarray_noalloc(self,
                            n: int | None,
                            size: int | None,
                            name: str,
                            start_idx: int | None,
                            qtype,
                            unknown_size=False):
        """Declares a quantum register without allocating new qubits.

        This function declares a register of `n` elements, where each element
        (or cell) consists of `size` qubits. Since no qubits are allocated, you
        must specify the starting qubit index via `start_idx`. If `start_idx`
        is `None`, the register will begin from the highest currently used
        qubit index. This behavior is particularly useful for capturing
        ancillary qubits that are automatically created by quantum subroutines.

        Additionally, by setting `unknown_size=True`, this function can be used
        to define ancillary qubits of unknown or dynamic size, such as those
        generated internally by a `QRoutine`.

        The `qtype` argument specifies how the register should be interpreted
        in quantum state analysis or visualization. It can be set to: - `bool`:
        interpret each element as a boolean value; - `int`: interpret each
        element as an integer; - `str`: display each element as a bitstring.

        Parameters:
            n (int): Number of elements in the register.
            size (int): Number of qubits per element.
            start_idx (int or None): Starting index for the register.
            unknown_size (bool): Whether the size is dynamic/unknown.
            qtype (type): Type used for interpreting qubit content (`bool`, `int`, or `str`).

        """

        key = f"{name}"
        start = start_idx if start_idx is not None else self._program.qbit_count
        if size is None:
            unknown_size = True
            n = None

        if unknown_size:
            stop = None
        else:
            stop = start_idx + size * n  # type: ignore
        self._qregnames_to_properties[key] = QRegsProperties(
            slice(start, stop), n, size, None, qtype, unknown_size)
