"""This gauss-jordan procedure is specifically tailored for ISD
"""
import logging

import numpy as np
from qat.lang.AQASM.gates import X, H
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

LOGGER = logging.getLogger(__name__)
# Just a fake swap for pictorial representation
FAKE = H


def get_required_ancillae(r: int):
    """Get the number of additional (swap_ancilla, add_ancilla) qubits required for
the RREF.

    :param nrows: Rows of matrix
    :param ncols: Cols of matrix
    :returns: (swap_ancilla, add_ancilla)

    """
    add_ancilla_n = r * (r - 1)
    # Add ancilla is necessary an even number
    swap_ancilla_n = int(add_ancilla_n / 2)
    return swap_ancilla_n, add_ancilla_n


@build_gate('GJISD', [int, int])
def get_rref(r, n, skip_rightmost=True):
    """Apply RREF to a matrix H.

    :param r: The number of rows of the original matrix H
    :param n: The number of cols of the original matrix H
    :param skip_rightmost: Skip the operations on the rightmost r*k submatrix (used in Prange)
    The gate takes as input, in this order:
    - The matrix (r * n), represented as qreg
    - The swap ancillae
    - The add ancillae

    The number of swap and add ancillae required can be obtained through the
    get_ancillae function.

    """
    qrout = QRoutine()

    qregs_rows = []
    for _ in range(r):
        qreg = qrout.new_wires(n)
        qregs_rows.append(qreg)

    r = min(r, n)
    swap_ancilla_n, add_ancilla_n = get_required_ancillae(r)
    swap_ancillae = qrout.new_wires(swap_ancilla_n)
    add_ancillae = qrout.new_wires(add_ancilla_n)
    add_ancilla_idx = 0
    swap_ancilla_idx = 0

    skip_cols = set()
    if skip_rightmost:
        skip_cols = set(range(r, n))
        print(skip_cols)

    for x in range(r):
        # impr. 1
        if x > 0:
            skip_cols.add(x-1)
            print(skip_cols)
        # we don't apply swap gates for the last row
        if x != r - 1:
            # improvement 3, X before starting all phases 1
            qrout.apply(X, qregs_rows[x][x])
            for i in range(x + 1, r):
                rowswap = get_row_swap(n, x, skip_cols.copy())
                qrout.apply(rowswap, qregs_rows[x], qregs_rows[i],
                            swap_ancillae[swap_ancilla_idx])
                swap_ancilla_idx += 1
            # improvement 3, X after finishing all phases 1
            qrout.apply(X, qregs_rows[x][x])

        # for i in range(r):
        #     if i == x:
        #         continue
        #     rowadd = get_row_addition(n, x, skip_cols)
        #     qrout.apply(rowadd, qregs_rows[i], qregs_rows[x],
        #                 add_ancillae[add_ancilla_idx])
        #     add_ancilla_idx += 1

    return qrout


@build_gate('ROWSWAP', [int, int, set])
def get_row_swap(n: int, pivot_idx: int, skip_cols: set):
    """WARN: the pivot element is checked agains state 1 (improvement 3)
    """
    qrout = QRoutine()
    pivot_row = qrout.new_wires(n)
    other_row = qrout.new_wires(n)
    anc = qrout.new_wires(1)
    qrout.apply(X.ctrl(), pivot_row[pivot_idx], anc)
    for c in range(n):
        if c not in skip_cols:
            qrout.apply(X.ctrl(2), anc, other_row[c], pivot_row[c])
        else:
            qrout.apply(FAKE.ctrl(2), anc, other_row[c], pivot_row[c])
    return qrout


@build_gate('ROWADD', [int, int, set])
def get_row_addition(n, pivot_idx: int, skip_cols:set):
    qrout = QRoutine()
    other_row = qrout.new_wires(n)
    pivot_row = qrout.new_wires(n)
    anc = qrout.new_wires(1)
    qrout.apply(X.ctrl(), other_row[pivot_idx], anc)
    for c in range(n):
        if c not in skip_cols:
            qrout.apply(X.ctrl(2), anc, pivot_row[c], other_row[c])
        else:
            qrout.apply(FAKE.ctrl(2), anc, other_row[c], pivot_row[c])
    return qrout


# @build_gate('ROWSWAP', [int, int, int])
# def _get_row_swap(nrows, ncols, row_src_idx: int):
#     """In reality just add to the source row the first row with non-zero element.
#     F.e., suppose:
#     - row_src_idx = 0
#     - rows = [[0, 1, 0], [1, 0, 0], [0, 1, 1]]

#     If rows[row_src_idx][row_src_idx] == 0: # True
#     - then we search for the first row (row_oth_idx) having a non-zero element
#       in the same row_src_idx # 1 in this case
#     - and then do rows[row_src_idx] += rows[row_oth_idx]

#     Note that the element of rows are qregister, each one representing a row.
#     Each qregister should have the same length, otw the result is undefined.

#     """
#     LOGGER.debug(f"nrows {nrows}, ncols {ncols}")
#     qfun = QRoutine()

#     # This will contain the source row
#     row_wires = []
#     for _ in range(nrows):
#         row_wires.append(qfun.new_wires(ncols))

#     # the pivot is on the diagonal
#     col_src_idx = row_src_idx
#     LOGGER.debug(f"row_src_idx {row_src_idx}")
#     row_src = row_wires[row_src_idx]
#     LOGGER.debug(f"row src {row_src}")
#     # LOGGER.debug(f"row src idxs {[q.index for q in row_src]}")
#     LOGGER.debug(f"X src {row_src[row_src_idx]} ")
#     qfun.apply(X, row_src[col_src_idx])
#     for row_oth_idx in range(row_src_idx + 1, nrows):
#         # All the possible rows after the source row
#         LOGGER.debug(f"row_oth_idx {row_oth_idx}")
#         row_oth = row_wires[row_oth_idx]
#         LOGGER.debug(f"row oth {row_oth}")
#         # LOGGER.debug(f"row oth idxs {[q.index for q in row_oth]}")

#         # Ancilla telling if the column must be swapped; since it's not reset
#         # to 0, I can't add it to the ancillae list
#         anc = qfun.new_wires(1)
#         # qfun.set_ancillae(anc)
#         # LOGGER.debug(f"ancillae {qfun.ancillae}")
#         LOGGER.debug(f"current ancilla {anc}")
#         # LOGGER.debug(f"current ancilla idx {anc[0].index}")
#         # CNOT where ctrl must be 0
#         # row_src[col_idx] can be 1 in two cases:
#         # - It has been set to 1 in the previous round following a swap
#         # - It was already 1 to start with
#         LOGGER.debug(f"CNOT {row_src[col_src_idx]} -> {anc} ")
#         qfun.apply(X.ctrl(), row_src[col_src_idx], anc)

#         # sum if ancilla is set, but only the col_idxs after the given one. The
#         # idea is that all previous idx are already at 0 bcz of previous row
#         # operations.
#         for col_idx in range(col_src_idx, ncols):
#             LOGGER.debug(
#                 f"CCNOT {anc}, {row_oth[col_idx]} -> {row_src[col_idx]} ")
#             qfun.apply(X.ctrl(2), anc, row_oth[col_idx], row_src[col_idx])

#     LOGGER.debug(f"X src {row_src[col_src_idx]} ")
#     qfun.apply(X, row_src[col_src_idx])
#     return qfun

# @build_gate('ROWADD', [int, int, int])
# def get_row_addition(nrows, ncols, row_src_idx: int):
#     qfun = QRoutine()
#     # nrows, ncols = len(matrix), len(matrix[0])
#     LOGGER.debug(f"nrows {nrows}, ncols {ncols}")

#     # This will contain the source row
#     # row_src = qfun.new_wires(row_length)
#     row_wires = []
#     for _ in range(nrows):
#         row_wires.append(qfun.new_wires(ncols))

#     col_src_idx = row_src_idx
#     LOGGER.debug(f"row_src_idx {row_src_idx}")
#     row_src = row_wires[row_src_idx]
#     LOGGER.debug(f"row src {row_src}")
#     # LOGGER.debug(f"row src idxs {[q.index for q in row_src]}")
#     # WIP diff, range
#     for row_oth_idx in range(nrows):
#         if row_oth_idx == row_src_idx:
#             continue
#         # All the possible rows after the source row
#         LOGGER.debug(f"row_oth_idx {row_oth_idx}")
#         row_oth = row_wires[row_oth_idx]
#         LOGGER.debug(f"row oth {row_oth}")
#         # LOGGER.debug(f"row oth idxs {[q.index for q in row_oth]}")
#         # Ancilla telling if the column must be swapped
#         anc = qfun.new_wires(1)
#         # qfun.set_ancillae(anc)
#         # LOGGER.debug(f"ancillae {qfun.ancillae}")
#         LOGGER.debug(f"current ancilla {anc}")
#         # LOGGER.debug(f"current ancilla idx {anc[0].index}")
#         # CNOT where ctrl must be 0
#         # row_src[col_idx] can be 1 in two cases:
#         # - It has been set to 1 in the previous round following a swap
#         # - It was already 1 to start with
#         LOGGER.debug(f"CNOT {row_src[col_src_idx]} -> {anc} ")
#         qfun.apply(X.ctrl(), row_oth[col_src_idx], anc)

#         # sum if ancilla is set, but only the col_idxs after the given one. The
#         # idea is that all previous idx are already at 0 bcz of previous row
#         # operations.
#         # WIP, diff, CCNOT src and tgt
#         for col_idx in range(col_src_idx, ncols):
#             LOGGER.debug(
#                 f"CCNOT {anc}, {row_oth[col_idx]} -> {row_src[col_idx]} ")
#             qfun.apply(X.ctrl(2), anc, row_src[col_idx], row_oth[col_idx])

#     LOGGER.debug("----")
#     return qfun
