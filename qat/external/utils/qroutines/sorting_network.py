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


def _build_gate_common(pattern: Dict[str, Any]) -> QRoutine:
    a_len: int = pattern['n_lines']
    comp_len: int = pattern['n_comps']
    routine = QRoutine()
    a_wires = routine.new_wires(a_len)
    comp_wires = routine.new_wires(comp_len)
    for swap_pattern in pattern['swaps_pattern']:
        # Compare qubits 1 and 2 and put the output in pattern 0
        routine.apply(two_bit_comparator(), a_wires[swap_pattern[1]],
                      a_wires[swap_pattern[2]], comp_wires[swap_pattern[0]])
        routine.apply(SWAP.ctrl(), comp_wires[swap_pattern[0]],
                      a_wires[swap_pattern[1]], a_wires[swap_pattern[2]])
    return routine


@build_gate("BITONIC_SORTER", [dict])
def build_gate_bitonic_sorter(pattern: Dict[str, Any]) -> QRoutine:
    return _build_gate_common(pattern)


def get_pattern_bitonic_sorter(n) -> Dict[str, Any]:
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

    _get_pattern_bitonic_sorter(0, initial_swaps, int(nwr_dict['n_lines'] / 2),
                                0, nwr_dict)
    nwr_dict['n_comps'] = len(nwr_dict['swaps_pattern'])
    return nwr_dict


def _get_pattern_bitonic_sorter(start, end, swap_step, comp_q_idx, nwr_dict):
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
    comp_q_idx = _get_pattern_bitonic_sorter(start, start + for_iter_next,
                                             int(swap_step / 2), comp_q_idx,
                                             nwr_dict)
    _LOGGER.debug(
        "Before rec, start: %d, end: %d, swap_step: %d, for_iter_next %d",
        start, end, swap_step, for_iter_next)
    comp_q_idx = _get_pattern_bitonic_sorter(start + swap_step,
                                             start + swap_step + for_iter_next,
                                             int(swap_step / 2), comp_q_idx,
                                             nwr_dict)
    return comp_q_idx


@build_gate("MERGER", [dict])
def build_gate_merger(pattern: dict):
    return _build_gate_common(pattern)


def get_pattern_merger(n):
    nwr_dict = {}
    comp_q_idx = _get_pattern_merger_support(n, nwr_dict, 0)

    nwr_dict['n_comps'] = len(nwr_dict['swaps_pattern'])
    return nwr_dict


def _get_pattern_merger_support(n, nwr_dict, comp_q_idx, start_shift=0):
    steps = int(np.ceil(np.log2(n)))
    nwr_dict['n_lines'] = 2**steps
    nwr_dict['swaps_pattern'] = nwr_dict.get('swaps_pattern', [])
    initial_swaps = int(nwr_dict['n_lines'] / 2)

    for i in range(initial_swaps):
        nwr_dict['swaps_pattern'].append(
            (comp_q_idx, i + start_shift,
             nwr_dict['n_lines'] - i - 1 + start_shift))
        comp_q_idx += 1

    # the second half of the circuit is identical to the bitonic sorter
    start = start_shift
    swap_step = int(initial_swaps / 2)
    comp_q_idx = _get_pattern_bitonic_sorter(start, start + swap_step,
                                             swap_step, comp_q_idx, nwr_dict)
    comp_q_idx = _get_pattern_bitonic_sorter(start + swap_step * 2,
                                             start + swap_step * 3, swap_step,
                                             comp_q_idx, nwr_dict)
    return comp_q_idx

@build_gate("SORTER", [dict])
def build_gate_sorter(pattern):
    return _build_gate_common(pattern)


def get_pattern_sorter(n):
    nwr_dict = {}
    lis = []
    print("")

    _get_pattern_sorter_support(0, n, lis)

    comp_q_idx = 0
    for (start, end) in reversed(lis):
        n = len(range(start, end))
        comp_q_idx = _get_pattern_merger_support(n, nwr_dict, comp_q_idx,
                                                 start)
    # for k, v in nwr_dict.items():
    #     print(k)
    #     print(v)
        nwr_dict['n_comps'] = len(nwr_dict['swaps_pattern'])
    return nwr_dict


def _get_pattern_sorter_support(start, end, acc, depth=0):
    rec_string = '>' * depth
    # print(f"{rec_string}recursion start")
    # print(f"{rec_string}merger [{start}-{end})")
    pattern = (start, end)
    acc.append(pattern)
    if (start + 2 >= end):
        # input(f"{rec_string}base case")
        return

    mid = int((start + end) / 2)
    # print(f"{rec_string}before recursion 1")
    _get_pattern_sorter_support(start, mid, acc, depth + 1)
    # print(f"{rec_string}before recursion 2")
    _get_pattern_sorter_support(mid, end, acc, depth + 1)
    return
