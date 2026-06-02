from typing import TYPE_CHECKING, Dict, List, Set, Tuple

import numpy as np
from qat.lang.AQASM.qbool import QBoolArray
from qat.lang.AQASM.qint import QInt
from kitqat.utils.bits.conversion import get_ints_from_bitstring

if TYPE_CHECKING:
    from qat.core.wrappers.result import Sample
    from qat.lang.AQASM.bits import QRegister
    from kitqat.qatmgmt.program import QArray


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


def extract_qarray_values_by_named_qarrays(
        named_qarrays: dict[str, 'QArray'],
        sample: "Sample") -> Dict[str, int | list[bool] | str]:
    """Given a Sample object, returns the state value for the register.
    """
    dicc = {}

    for name, qarray in named_qarrays.items():
        bitstring = sample.state.bitstring[named_qarrays[name].slic]
        if qarray.qtype == int:
            assert qarray.n
            assert qarray.m
            value = get_ints_from_bitstring(bitstring, qarray.n, qarray.m,
                                            False)
        elif qarray.qtype == bool:
            value = []
            for bit in bitstring:
                value.append(bool(int(bit)))
        else:
            value = bitstring
        dicc[name] = value
    return dicc


def build_matrix_from_sample(sample: "Sample", qreg_range: Set[int],
                             shape: Tuple[int, int]) -> np.ndarray:
    return build_matrix_from_bitstring(sample.state.bitstring, qreg_range,
                                       shape)


def build_matrix_from_bitstring(bitstring: str, qreg_range: Set[int],
                                shape: Tuple[int, int]) -> np.ndarray:
    matrix = np.zeros(shape, dtype=np.ubyte)
    interesting_bits = [
        val for i, val in enumerate(bitstring) if i in qreg_range
    ]
    for i, val in enumerate(interesting_bits):
        row = i // shape[1]
        col = i % shape[1]
        matrix[row][col] = val
    return matrix


def build_u_matrix_from_sample(sample, nsquare):
    """Build the matrix of transformations applied to obtain the RREF. I.e., if
    original matrix was A and its RREF is B, we have U * B = A.

    This function will return the U matrix by analyzing the intermediate
    measurements on the ancilla (swap and add) qubits produced by the RREF
    gate.

    """
    if len(sample.intermediate_measurements) != 2:
        return
    # this creates a bitlist
    inter_meas_aout, inter_meas_bout = [
        i.cbits for i in sample.intermediate_measurements
    ]
    return build_u_matrix_from_bitlists(inter_meas_aout, inter_meas_bout,
                                        nsquare)


def build_u_matrix_from_bitstrings(swaps: str, adds: str, nsquare):
    return build_u_matrix_from_bitlists([int(i) for i in swaps],
                                        [int(i) for i in adds], nsquare)


def build_u_matrix_from_bitlists(swaps: list, adds: list, nsquare):
    """Build the matrix of transformations applied to obtain the RREF. I.e., if
    original matrix was A and its RREF is B, we have U * B = A.

    This function will return the U matrix by analyzing the ancilla qubits
    produced by the RREF gate.

    """
    swap_idx = 0
    add_idx = 0
    u = np.eye(nsquare, dtype=np.uint8)
    for i in range(nsquare):
        for j in range(i + 1, nsquare):
            if swaps[swap_idx]:
                u[
                    i,
                ] += u[
                    j,
                ]
            swap_idx += 1
        for j in range(nsquare):
            if j == i:
                continue
            if adds[add_idx]:
                u[
                    j,
                ] += u[
                    i,
                ]
            add_idx += 1
    u = u % 2
    return u
