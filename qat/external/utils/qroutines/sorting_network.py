"""
See http://staff.ustc.edu.cn/~csli/graduate/algorithms/book6/chap28.htm
"""
import logging
from typing import Any, Dict

import numpy as np
from qat.external.utils.qroutines.adder import two_bit_comparator
from qat.lang.AQASM.gates import SWAP
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

_LOGGER = logging.getLogger(__name__)


@build_gate("SWAP_COLS", [int])
def build_gate_swap_cols(nrows):
    routine = QRoutine()
    col1 = routine.new_wires(nrows)
    col2 = routine.new_wires(nrows)

    for wire1, wire2 in zip(col1, col2):
        routine.apply(SWAP, wire1, wire2)

    return routine


@build_gate("SORTING_NETWORK_COLS", [int, dict])
def build_gate_sorting_network_cols(
        nrows: int, benes_pattern_dict: Dict[str, Any]) -> QRoutine:
    ncols: int = benes_pattern_dict['n_lines']
    comp_len: int = benes_pattern_dict['n_comps']

    routine = QRoutine()
    row_wires = []
    for _ in range(nrows):
        row_wires.append(routine.new_wires(ncols))
    col_wires = []
    for col_idx in range(ncols):
        col_wires.append(list([qr[col_idx] for qr in row_wires]))
    comp = routine.new_wires(comp_len)

    qrout = build_gate_swap_cols(nrows)
    for pattern in benes_pattern_dict['swaps_pattern']:
        routine.apply(qrout.ctrl(), comp[pattern[0]], col_wires[pattern[1]],
                      col_wires[pattern[2]])

    return routine


@build_gate("BITONIC_SORTING", [dict])
def build_gate_bitnonic_sorting(
        benes_pattern_dict: Dict[str, Any]) -> QRoutine:
    a_len: int = benes_pattern_dict['n_lines']
    comp_len: int = benes_pattern_dict['n_comps']
    routine = QRoutine(arity=a_len + comp_len)
    # We use numbers directly, not wires
    for pattern in benes_pattern_dict['swaps_pattern']:
        # Compare qubits 1 and 2 and put the output in pattern 0
        routine.apply(two_bit_comparator(), pattern[1], pattern[2],
                      a_len + pattern[0])
        routine.apply(SWAP.ctrl(), a_len + pattern[0], pattern[1], pattern[2])
    return routine


def get_pattern_bitonic_sorting(n) -> Dict[str, Any]:
    """Given how it's built, n should be a power of 2 and, if not, it returns the
    combination rounding up to the top power of 2. If the original n is not a
    power of 2, you may want to adapt the circuit avoiding the use of the last
    bits.

    Returns a dictionary containing the:
    1. n_lines, the number of lines required; it is the rounding up of n to the
    closest power of 2

    2. n_comps, the number of fair coin flips required to obtain the full
    permutation

    3. the swaps_pattern, i.e. a list of tuples containing:
    - an integer signalling which comparator output bit to use
    - the first line involved in the swap
    - the second line involved in the swap
    """
    nwr_dict = {}
    steps = int(np.ceil(np.log2(n)))
    nwr_dict['n_lines'] = 2**steps
    nwr_dict['swaps_pattern'] = []
    initial_swaps = int(nwr_dict['n_lines'] / 2)

    _get_pattern_bitonic_network(0, initial_swaps,
                                 int(nwr_dict['n_lines'] / 2), 0, nwr_dict)
    nwr_dict['n_comps'] = len(nwr_dict['swaps_pattern'])
    return nwr_dict


def _get_generate_pattern_support_step2(start, end, swap_step, comp_q_idx,
                                        nwr_dict):

    pass


def _get_generate_pattern_support_step3(start, end, swap_step, comp_q_idx,
                                        nwr_dict):
    pass


def _get_pattern_bitonic_network(start, end, swap_step, comp_q_idx, nwr_dict):
    _LOGGER.debug("Start: %d, end: %d, swap_step: %d", start, end, swap_step)
    if (swap_step == 0 or start >= end):
        _LOGGER.debug("Base case recursion")
        return comp_q_idx

    for_iter = 0
    for i in range(start, end):
        for_iter += 1
        _LOGGER.info("cswap(%d, %d, %d)", comp_q_idx, i, i + swap_step)
        nwr_dict['swaps_pattern'].append((comp_q_idx, i, i + swap_step))
        comp_q_idx += 1

    for_iter_next = min(for_iter, int(swap_step / 2))
    _LOGGER.debug(
        "Before rec1, start: %d, end: %d, swap_step: %d, for_iter_next %d",
        start, end, swap_step, for_iter_next)
    comp_q_idx = _get_pattern_bitonic_network(start, start + for_iter_next,
                                              int(swap_step / 2), comp_q_idx,
                                              nwr_dict)
    _LOGGER.debug(
        "Before rec, start: %d, end: %d, swap_step: %d, for_iter_next %d",
        start, end, swap_step, for_iter_next)
    comp_q_idx = _get_pattern_bitonic_network(
        start + swap_step, start + swap_step + for_iter_next,
        int(swap_step / 2), comp_q_idx, nwr_dict)
    return comp_q_idx
