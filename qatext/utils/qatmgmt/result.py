from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from qat.lang.AQASM import Result


def get_state_vector_from_result(res: "Result", nqubits: int) -> np.array:
    state_vec = np.zeros(2**nqubits, dtype=np.complex256)
    for sample in res:
        state_dec = sample.state.state
        state_vec[state_dec] = sample.amplitude
    return state_vec


def get_sample_for_basis_dec_from_result(res: "Result",
                                         basis_state_dec: int,
                                         little_endian=False):
    attr = "lsb_int" if little_endian else "int"
    for sample in res:
        if getattr(sample.state, attr) == basis_state_dec:
            return sample
        # This is true if we assume that the samples are
        # put in the result list in order
        # Apparently NOT true in the QLM, so full search is needed
        # elif sample.state.state > basis_state_dec:
        #     return None
    return None


def get_sample_for_basis_str_from_result(res: "Result", basis_str_dec: int):
    for sample in res:
        if sample.state.bitstring == basis_str_dec:
            return sample
    return None
