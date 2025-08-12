from typing import TYPE_CHECKING, Dict, List

from qat.lang.AQASM.qbool import QBoolArray
from qat.lang.AQASM.qint import QInt

if TYPE_CHECKING:
    from qat.core.wrappers.result import Sample
    from qat.lang.AQASM.bits import QRegister
    from qatext.qatmgmt.program import QRegsProperties


def extract_qubit_bitstring(qbit_idxs: List[int], sample: "Sample") -> str:
    interesting_vals = [
        val for i, val in enumerate(sample.state.bitstring) if i in qbit_idxs
    ]
    return "".join(interesting_vals)


def extract_qreg_bitstring(register: "QRegister", sample: "Sample") -> str:
    """Given a Sample object, returns the bitstring for the register."""
    return sample.state.bitstring[register.start:register.start +
                                  register.length]


def extract_qregs_bitstring(registers: List["QRegister"],
                            sample: "Sample") -> List[str]:
    """Given a Sample object, returns the bitstring for each register."""
    liss = []
    for reg in registers:
        liss.append(extract_qreg_bitstring(reg, sample))
    return liss


def extract_qreg_bitstrings_by_names(name_to_reg: Dict[str, "QRegister"],
                                     sample: "Sample") -> Dict[str, str]:
    """Given a Sample object, returns the bitstring for each register.

    The name_to_reg dictionary contains all the wanted qregs, together
    with their names. To note that this dictionary should be prepared in
    advance.
    """
    dicc = {}
    for name, reg in name_to_reg.items():
        dicc[name] = extract_qreg_bitstring(reg, sample)
    return dicc


def extract_qreg_value(register: "QRegister", sample: "Sample") -> str:
    """Given a Sample object, returns the state value for the register.
    Warning: this only works for quantum registers created through the Program
    qalloc routine. That is, it does not work with externally defined list of
    qubits.

    """
    for idx, qreg in enumerate(sample.state.qregs):
        if register == qreg:
            return sample.state.value[idx]
    raise Exception("Register not found")


def extract_qreg_values_by_names(
        name_to_reg: Dict[str, "QRegister"],
        sample: "Sample") -> Dict[str, int | bool | str]:
    """Given a Sample object, returns the state value for the register.
    """
    dicc = {}
    for name, reg in name_to_reg.items():
        bitstring = extract_qreg_bitstring(reg, sample)
        if isinstance(reg, QInt):
            value = int(bitstring, 2)
        elif isinstance(reg, QBoolArray):
            value = []
            for bit in bitstring:
                value.append(bool(int(bit)))
        else:
            value = bitstring
        dicc[name] = value
    return dicc

def extract_qreg_values_by_qregs_properties(
            qregs_properties: dict[str, 'QRegsProperties'],
            sample: "Sample") -> Dict[str, int | list[bool] | str]:
    """Given a Sample object, returns the state value for the register.
    """
    dicc = {}

    for name, qreg_properties in qregs_properties.items():
        bitstring = sample.state.bitstring[qregs_properties[name].slic]
        if qreg_properties.qtype == int:
            value = int(bitstring, 2)
        elif qreg_properties.qtype == bool:
            value = []
            for bit in bitstring:
                value.append(bool(int(bit)))
        else:
            value = bitstring
        dicc[name] = value
    return dicc
