from typing import TYPE_CHECKING, Dict, List

import numpy as np

if TYPE_CHECKING:
    from qat.lang.AQASM import Result
    from qat.lang.AQASM.bits import QRegister
    from qat.core.wrappers.result import Sample


def get_state_vector_from_result(res: 'Result', nqubits: int) -> np.array:
    state_vec = np.zeros(2**nqubits, dtype=np.complex256)
    for sample in res.raw_data:
        state_dec = sample.state.state
        state_vec[state_dec] = sample.amplitude
    return state_vec


def get_sample_for_basis_dec_from_res(res: 'Result',
                                      basis_state_dec: int,
                                      little_endian=False):
    attr = 'lsb_int' if little_endian else 'int'
    for sample in res.raw_data:
        if getattr(sample.state, attr) == basis_state_dec:
            return sample
        # This is true if we assume that the samples are
        # put in the result list in order
        # Apparently NOT true in the QLM, so full search is needed
        # elif sample.state.state > basis_state_dec:
        #     return None
    return None


def get_sample_for_basis_str_from_res(res: 'Result', basis_str_dec: int):
    for sample in res.raw_data:
        if sample.state.bitstring == basis_str_dec:
            return sample
    return None


def get_qreg_name_to_bitstring_from_sample(name_to_reg: Dict[str, 'QRegister'],
                                           sample: 'Sample') -> Dict[str, str]:
    """Given a Sample object, returns the bitstring for each register. The
    name_to_reg dictionary contains all the wanted qregs, together with their
    names. To note that this dictionary should be prepared in advance.
    """
    dicc = {}
    for name, reg in name_to_reg.items():
        dicc[name] = get_qreg_to_bitstring_from_sample(reg, sample)
    return dicc


def get_qregs_to_bitstring_from_sample(registers: List['QRegister'],
                                       sample: 'Sample') -> List[str]:
    """Given a Sample object, returns the bitstring for each register.
    """
    liss = []
    for reg in registers:
        liss.append(get_qreg_to_bitstring_from_sample(reg, sample))
    return liss


def get_qreg_to_bitstring_from_sample(register: 'QRegister',
                                      sample: 'Sample') -> str:
    """Given a Sample object, returns the bitstring for the register.
    """
    # TODO maybe we can directly use the sample.state.qregs index object
    return sample.state.bitstring[register.start:register.start +
                                  register.length]


# TODO same as before, idk why it's here; check which program is using it
# def get_qreg_bitstring_from_sample(qreg: 'QRegister', sample: 'Sample') -> str:
#     """Given a Sample object, returns the bitstring for the register.
#     """
#     return sample.state.bitstring[qreg.start:qreg.start + qreg.length]



def get_qbits_to_bitstring_from_sample(qbit_idxs: List[int], sample: 'Sample') -> str:
    print(qbit_idxs)
    interesting_vals = [
        val for i, val in enumerate(sample.state.bitstring) if i in qbit_idxs
    ]
    print(interesting_vals)
    return ''.join(interesting_vals)
