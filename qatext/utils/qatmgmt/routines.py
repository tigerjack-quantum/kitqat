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

    def qregs_array_wires(
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
