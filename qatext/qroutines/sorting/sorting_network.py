"""See http://staff.ustc.edu.cn/~csli/graduate/algorithms/book6/chap28.htm and
https://fileadmin.cs.lth.se/cs/Personal/Rolf_Karlsson/lect10.pdf for reference.

The original work is in Chapter 27.3,4,5 of T. H. Cormen, C. E.
Leiserson, R. L. Rivest, and C. Stein, Introduction to algorithms,
second edition. The MIT Press and McGraw-Hill Book Company, 2001.
"""
from typing import Any, Dict, List, Tuple
import logging
import numpy as np

from qat.lang.AQASM.gates import SWAP, CNOT, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

_LOGGER = logging.getLogger(__name__)


# ============================================================
# Utilities
# ============================================================

def _filter_and_reindex_swaps(
    swaps: List[Tuple[int, int, int]], n_valid: int
) -> List[Tuple[int, int, int]]:
    """
    Remove swaps touching invalid wires and reindex comparator ids.
    """
    filtered = [(c, i, j) for (c, i, j) in swaps if i < n_valid and j < n_valid]

    # Reindex comparator ids
    new_swaps = []
    for new_idx, (_, i, j) in enumerate(filtered):
        new_swaps.append((new_idx, i, j))

    return new_swaps


# ============================================================
# Circuit builder
# ============================================================

def _build_gate_common(net_data: Dict[str, Any], to_compare=True, to_reverse=False) -> QRoutine:
    """to_permute can be set to false in case one wants only to compare the
    qubits as per a sorting network, but then instead doesn't want to swap."""
    a_len: int = net_data["n_lines"]
    comp_len: int = net_data["n_comps"]

    routine = QRoutine()
    a_wires = routine.new_wires(a_len)
    comp_wires = routine.new_wires(comp_len)

    if to_compare and not to_reverse:
        for qb in a_wires:
            routine.apply(X, qb)

    for comp_idx, i, j in net_data["swaps_pattern"]:
        a_qb = a_wires[i]
        b_qb = a_wires[j]
        ctrl_qb = comp_wires[comp_idx]

        # Optimized comparator
        if to_compare:
            routine.apply(CNOT, b_qb, ctrl_qb)
        routine.apply(SWAP.ctrl(), ctrl_qb, a_qb, b_qb)

    if to_compare and not to_reverse:
        for qb in a_wires:
            routine.apply(X, qb)

    return routine


# ============================================================
# Bitonic sorter
# ============================================================

# @build_gate("BITONIC_SORTER", [dict])
def build_gate_bitonic_sorter(net_data: Dict[str, Any]) -> QRoutine:
    return _build_gate_common(net_data)


def get_pattern_bitonic_sorter(n: int) -> Dict[str, Any]:
    net_data: Dict[str, Any] = {}

    steps = int(np.ceil(np.log2(n)))
    n_lines_pow2 = 2**steps

    net_data["n_lines"] = n_lines_pow2
    net_data["swaps_pattern"] = []

    _get_pattern_bitonic_sorter(
        0,
        n_lines_pow2 // 2,
        n_lines_pow2 // 2,
        0,
        net_data,
    )

    # Filter + reindex
    swaps = _filter_and_reindex_swaps(net_data["swaps_pattern"], n)

    net_data["swaps_pattern"] = swaps
    net_data["n_comps"] = len(swaps)
    net_data["n_lines"] = n  # final visible size

    return net_data


def _get_pattern_bitonic_sorter(start, end, swap_step, comp_q_idx, net_data):
    if swap_step == 0 or start >= end:
        return comp_q_idx

    for i in range(start, end):
        net_data["swaps_pattern"].append((comp_q_idx, i, i + swap_step))
        comp_q_idx += 1

    next_len = min(end - start, swap_step // 2)

    comp_q_idx = _get_pattern_bitonic_sorter(
        start,
        start + next_len,
        swap_step // 2,
        comp_q_idx,
        net_data,
    )

    comp_q_idx = _get_pattern_bitonic_sorter(
        start + swap_step,
        start + swap_step + next_len,
        swap_step // 2,
        comp_q_idx,
        net_data,
    )

    return comp_q_idx


# ============================================================
# Merger
# ============================================================

@build_gate("MERGER", [dict])
def build_gate_merger(net_data: dict):
    return _build_gate_common(net_data)


def get_pattern_merger(n: int) -> Dict[str, Any]:
    net_data: Dict[str, Any] = {}

    _get_pattern_merger_support(n, net_data, 0)

    # Filter + reindex
    swaps = _filter_and_reindex_swaps(net_data["swaps_pattern"], n)

    net_data["swaps_pattern"] = swaps
    net_data["n_comps"] = len(swaps)
    net_data["n_lines"] = n

    return net_data


def _get_pattern_merger_support(n, net_data, comp_q_idx, start_shift=0):
    steps = int(np.ceil(np.log2(n)))
    n_lines_pow2 = 2**steps

    net_data["n_lines"] = n_lines_pow2
    net_data["swaps_pattern"] = net_data.get("swaps_pattern", [])

    half = n_lines_pow2 // 2

    # First stage
    for i in range(half):
        net_data["swaps_pattern"].append(
            (comp_q_idx, i + start_shift, n_lines_pow2 - i - 1 + start_shift)
        )
        comp_q_idx += 1

    # Bitonic stages
    swap_step = half // 2

    comp_q_idx = _get_pattern_bitonic_sorter(
        start_shift,
        start_shift + swap_step,
        swap_step,
        comp_q_idx,
        net_data,
    )

    comp_q_idx = _get_pattern_bitonic_sorter(
        start_shift + 2 * swap_step,
        start_shift + 3 * swap_step,
        swap_step,
        comp_q_idx,
        net_data,
    )

    return comp_q_idx


# ============================================================
# Full sorter
# ============================================================

# @build_gate("SORTER", [dict])
def build_gate_sorter(net_data, to_compare=True, to_reverse=False):
    return _build_gate_common(net_data, to_compare=to_compare, to_reverse=to_reverse)

def get_pattern_sorter(n: int) -> Dict[str, Any]:
    net_data: Dict[str, Any] = {}
    intervals: List[Tuple[int, int]] = []

    _get_pattern_sorter_support(0, n, intervals)

    comp_q_idx = 0

    for start, end in reversed(intervals):
        size = end - start
        comp_q_idx = _get_pattern_merger_support(
            size, net_data, comp_q_idx, start
        )

    # Final filtering
    swaps = _filter_and_reindex_swaps(net_data["swaps_pattern"], n)

    net_data["swaps_pattern"] = swaps
    net_data["n_comps"] = len(swaps)
    net_data["n_lines"] = n

    return net_data


def _get_pattern_sorter_support(start, end, acc):
    acc.append((start, end))

    if start + 2 >= end:
        return

    mid = (start + end) // 2

    _get_pattern_sorter_support(start, mid, acc)
    _get_pattern_sorter_support(mid, end, acc)
