from typing import TYPE_CHECKING, Dict, List
import numpy as np


if TYPE_CHECKING:
    from qat.lang.AQASM.bits import QRegister
    from qat.core.wrappers.result import Sample

def get_qreg_name_to_bitstring_from_sample(
    name_to_reg: Dict[str, "QRegister"], sample: "Sample"
) -> Dict[str, str]:
    """Given a Sample object, returns the bitstring for each register.

    The name_to_reg dictionary contains all the wanted qregs, together
    with their names. To note that this dictionary should be prepared in
    advance.
    """
    dicc = {}
    for name, reg in name_to_reg.items():
        dicc[name] = get_qreg_to_bitstring_from_sample(reg, sample)
    return dicc


def get_qregs_to_bitstring_from_sample(
    registers: List["QRegister"], sample: "Sample"
) -> List[str]:
    """Given a Sample object, returns the bitstring for each register."""
    liss = []
    for reg in registers:
        liss.append(get_qreg_to_bitstring_from_sample(reg, sample))
    return liss


def get_qreg_to_bitstring_from_sample(register: "QRegister", sample: "Sample") -> str:
    """Given a Sample object, returns the bitstring for the register."""
    # TODO maybe we can directly use the sample.state.qregs index object
    return sample.state.bitstring[register.start : register.start + register.length]


def get_qbits_to_bitstring_from_sample(qbit_idxs: List[int], sample: "Sample") -> str:
    interesting_vals = [
        val for i, val in enumerate(sample.state.bitstring) if i in qbit_idxs
    ]
    return "".join(interesting_vals)
