import logging
from typing import TYPE_CHECKING, List, Set, Tuple

import numpy as np
from qat.external.utils.qatmgmt.results import (
    get_qbits_to_bitstring_from_sample, get_qreg_to_bitstring_from_sample)
from qat.lang.AQASM.gates import X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

if TYPE_CHECKING:
    from qat.lang.AQASM import Result, QRegister

LOGGER = logging.getLogger(__name__)


def build_rref_matrix_from_result(res: 'Result', qreg_range: Set[int],
                                  shape: Tuple[int, int]):
    sample = res.raw_data[0]
    # vals = get_qbits_to_bitstring_from_sample(qreg_range, sample)

    matrix = np.zeros(shape, dtype=np.ubyte)
    interesting_bits = [
        val for i, val in enumerate(sample.state.bitstring) if i in qreg_range
    ]
    for i, val in enumerate(interesting_bits):
        row = i // shape[1]
        col = i % shape[1]
        matrix[row][col] = val

    return matrix


# TODO: Ideas
# 2. Avoid additional ancillae
#    - In the swap stage, do not take care of the pivot cell: it'll always be 1 at the end. We can just use Use additional `n` qubits initialized to 1. The pivot cell are still necessary as controllers for all the row operations.
#    - In the same way, when adding the pivot row to all the other rows (in order to put all 0's above and below)


# @build_gate("RowSwap", [int, int, int, List])
@build_gate('ROWSWAP', [List, int])
def get_row_swap(matrix: List[List[int]], row_src_idx: int):
@build_gate('ROWSWAP', [int, int, int])
def get_row_swap(nrows, ncols, row_src_idx: int):
    """In reality just add to the source row the first row with non-zero element.
    F.e., suppose:
    - row_src_idx = 0
    - rows = [[0, 1, 0], [1, 0, 0], [0, 1, 1]]

    If rows[row_src_idx][row_src_idx] == 0: # True
    - then we search for the first row (row_oth_idx) having a non-zero element in the same row_src_idx # 1 in this case
    - and then do rows[row_src_idx] += rows[row_oth_idx]

    Note that the element of rows are qregister, each one representing a row.
    Each qregister should have the same length, otw the result is undefined.

    """
    LOGGER.debug(f"nrows {nrows}, ncols {ncols}")
    qfun = QRoutine()

    # This will contain the source row
    row_wires = []
    for _ in range(nrows):
        row_wires.append(qfun.new_wires(ncols))

    # the pivot is on the diagonal
    col_src_idx = row_src_idx
    LOGGER.debug(f"row_src_idx {row_src_idx}")
    row_src = row_wires[row_src_idx]
    LOGGER.debug(f"row src {row_src}")
    # LOGGER.debug(f"row src idxs {[q.index for q in row_src]}")
    for row_oth_idx in range(row_src_idx + 1, nrows):
        # All the possible rows after the source row
        LOGGER.debug(f"row_oth_idx {row_oth_idx}")
        row_oth = row_wires[row_oth_idx]
        LOGGER.debug(f"row oth {row_oth}")
        # LOGGER.debug(f"row oth idxs {[q.index for q in row_oth]}")

        # Ancilla telling if the column must be swapped; since it's not reset
        # to 0, I can't add it to the ancillae list
        anc = qfun.new_wires(1)
        # qfun.set_ancillae(anc)
        # LOGGER.debug(f"ancillae {qfun.ancillae}")
        LOGGER.debug(f"current ancilla {anc}")
        # LOGGER.debug(f"current ancilla idx {anc[0].index}")
        # CNOT where ctrl must be 0
        # row_src[col_idx] can be 1 in two cases:
        # - It has been set to 1 in the previous round following a swap
        # - It was already 1 to start with
        LOGGER.debug(f"X src {row_src[row_src_idx]} ")
        qfun.apply(X, row_src[col_src_idx])
        LOGGER.debug(f"CNOT {row_src[col_src_idx]} -> {anc} ")
        qfun.apply(X.ctrl(), row_src[col_src_idx], anc)
        LOGGER.debug(f"X src {row_src[col_src_idx]} ")
        qfun.apply(X, row_src[col_src_idx])

        # sum if ancilla is set, but only the col_idxs after the given one. The
        # idea is that all previous idx are already at 0 bcz of previous row
        # operations.
        for col_idx in range(col_src_idx, ncols):
            LOGGER.debug(
                f"CCNOT {anc}, {row_oth[col_idx]} -> {row_src[col_idx]} ")
            qfun.apply(X.ctrl(2), anc, row_oth[col_idx], row_src[col_idx])

    return qfun


@build_gate('ROWADD', [int, int, int])
def get_row_addition(nrows, ncols, row_src_idx: int):
    qfun = QRoutine()
    # nrows, ncols = len(matrix), len(matrix[0])
    LOGGER.debug(f"nrows {nrows}, ncols {ncols}")

    # This will contain the source row
    # row_src = qfun.new_wires(row_length)
    row_wires = []
    for _ in range(nrows):
        row_wires.append(qfun.new_wires(ncols))

    col_src_idx = row_src_idx
    LOGGER.debug(f"row_src_idx {row_src_idx}")
    row_src = row_wires[row_src_idx]
    LOGGER.debug(f"row src {row_src}")
    # LOGGER.debug(f"row src idxs {[q.index for q in row_src]}")
    # WIP diff, range
    for row_oth_idx in range(nrows):
        if row_oth_idx == row_src_idx:
            continue
        # All the possible rows after the source row
        LOGGER.debug(f"row_oth_idx {row_oth_idx}")
        row_oth = row_wires[row_oth_idx]
        LOGGER.debug(f"row oth {row_oth}")
        # LOGGER.debug(f"row oth idxs {[q.index for q in row_oth]}")
        # Ancilla telling if the column must be swapped
        anc = qfun.new_wires(1)
        # qfun.set_ancillae(anc)
        # LOGGER.debug(f"ancillae {qfun.ancillae}")
        LOGGER.debug(f"current ancilla {anc}")
        # LOGGER.debug(f"current ancilla idx {anc[0].index}")
        # CNOT where ctrl must be 0
        # row_src[col_idx] can be 1 in two cases:
        # - It has been set to 1 in the previous round following a swap
        # - It was already 1 to start with
        LOGGER.debug(f"CNOT {row_src[col_src_idx]} -> {anc} ")
        qfun.apply(X.ctrl(), row_oth[col_src_idx], anc)

        # sum if ancilla is set, but only the col_idxs after the given one. The
        # idea is that all previous idx are already at 0 bcz of previous row
        # operations.
        # WIP, diff, CCNOT src and tgt
        for col_idx in range(col_src_idx, ncols):
            LOGGER.debug(
                f"CCNOT {anc}, {row_oth[col_idx]} -> {row_src[col_idx]} ")
            qfun.apply(X.ctrl(2), anc, row_src[col_idx], row_oth[col_idx])

    LOGGER.debug("----")
    return qfun
