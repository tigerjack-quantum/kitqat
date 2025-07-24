# TODO change location of QRegsProperties
from typing import Type, Union

from qat.lang.AQASM.qbool import QBoolArray
from qat.lang.AQASM.qint import QInt
from qatext.utils.qatmgmt.program import QRegsProperties


class QRoutineWrapper:

    def __init__(self, qroutine_instance):
        self._qroutine = qroutine_instance
        self._qregnames_to_properties: dict[str, QRegsProperties] = {}

    def __getattr__(self, name):
        return getattr(self._qroutine, name)

    def qarray_wires(
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
            qr = self._qroutine.new_wires(size, qtype_myqlm)
            regs.append(qr)
        key = f"{name}"
        start = regs[0][0].index
        stop = regs[-1][-1].index + 1
        self._qregnames_to_properties[key] = QRegsProperties(
            slice(start, stop), n, size, regs, qtype)
        return regs

    def qarray_wires_noalloc(self,
                            n: int | None,
                            size: int | None,
                            name: str,
                            start_idx: int | None,
                            qtype,
                            unknown_size=False):
        """Declares a quantum register without creating new QRoutine wires.

        This function declares a register of `n` elements, where each element
        (or cell) consists of `size` qubits. Since no qubits are allocated, you
        must specify the starting qubit index via `start_idx`. If `start_idx`
        is `None`, the register will begin from the highest currently used
        qubit index. This behavior is particularly useful for capturing
        ancillary qubits that are automatically created by quantum subroutines.

        Additionally, by setting `unknown_size=True`, this function can be used
        to define ancillary qubits of unknown or dynamic size, such as those
        generated internally by a `QRoutine`.

        The `qtype` argument specifies how the register should be interpreted in
        quantum state analysis or visualization. It can be set to:
        - `bool`: interpret each element as a boolean value;
        - `int`: interpret each element as an integer;
        - `str`: display each element as a bitstring.

        Parameters:
            n (int): Number of elements in the register.
            size (int): Number of qubits per element.
            start_idx (int or None): Starting index for the register.
            unknown_size (bool): Whether the size is dynamic/unknown.
            qtype (type): Type used for interpreting qubit content (`bool`, `int`, or `str`).

        """
        key = f"{name}"
        start = start_idx if start_idx is not None else self._qroutine.max_wire + 1
        if size is None:
            unknown_size = True
            n = None

        if unknown_size:
            stop = None
        else:
            stop = start_idx + size * n  # type: ignore
        self._qregnames_to_properties[key] = QRegsProperties(
            slice(start, stop), n, size, None, qtype, unknown_size)
