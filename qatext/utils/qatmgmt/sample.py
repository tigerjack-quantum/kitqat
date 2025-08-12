from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from qat.lang.AQASM.bits import QRegister
    from qat.core.wrappers.result import Sample


def extract_qregs_bitstring(registers: List["QRegister"],
                            sample: "Sample") -> List[str]:
    """Given a Sample object, returns the bitstring for each register."""
    liss = []
    for reg in registers:
        liss.append(extract_qreg_bitstring(reg, sample))
    return liss


def extract_qreg_bitstring(register: "QRegister", sample: "Sample") -> str:
    """Given a Sample object, returns the bitstring for the register."""
    # TODO maybe we can directly use the sample.state.qregs index object
    return sample.state.bitstring[register.start:register.start +
                                  register.length]


def extract_qubit_bitstring(qbit_idxs: List[int], sample: "Sample") -> str:
    interesting_vals = [
        val for i, val in enumerate(sample.state.bitstring) if i in qbit_idxs
    ]
    return "".join(interesting_vals)



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
