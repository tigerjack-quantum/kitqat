"""This gauss-jordan procedure is specifically tailored for ISD It contains
optimization 5 only w.r.t.

the other one, which does not seem t provide any benefit
"""
import logging

from qat.lang.AQASM.gates import H, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

LOGGER = logging.getLogger(__name__)
# Just a fake swap for pictorial representation
FAKE = H


def get_required_ancillae(r: int):
    """Get the number of additional (swap_ancilla, add_ancilla) qubits required
    for the RREF.

    :param nrows: Rows of matrix
    :param ncols: Cols of matrix
    :returns: (swap_ancilla, add_ancilla)
    """
    add_ancilla_n = r * (r - 1)
    # Add ancilla is necessary an even number
    swap_ancilla_n = int(add_ancilla_n / 2)
    return swap_ancilla_n, add_ancilla_n


@build_gate("GJISD", [int, int])
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

    for x in range(r):
        # impr. 1
        if x > 0:
            skip_cols.add(x - 1)
        # we don't apply swap gates for the last row
        if x != r - 1:
            # improvement 3, X before starting all phases 1
            qrout.apply(X, qregs_rows[x][x])
            for i in range(x + 1, r):
                # rowswap = get_row_swap(n, x, skip_cols.copy())
                # ctrl = swap_ancillae[swap_ancilla_idx]
                # qrout.apply(rowswap, qregs_rows[x], qregs_rows[i], ctrl)
                #
                qrout.apply(X.ctrl(), qregs_rows[x][x], swap_ancillae[swap_ancilla_idx])
                qrout_xor = get_cell_xor(2)
                _skip_cols_c = skip_cols.copy()
                nxors = 0
                for c in range(n):
                    # skip  not only columsn, but also pivot element. We postpone it to last op for impr. 5
                    if c not in _skip_cols_c and c != x:
                        ctrl = (
                            swap_ancillae[swap_ancilla_idx]
                            if nxors % 2
                            else qregs_rows[x][x]
                        )
                        # qrout.apply(X.ctrl(2), anc, other_row[c], pivot_row[c])
                        qrout.apply(qrout_xor, ctrl, qregs_rows[i][c], qregs_rows[x][c])
                        nxors += 1
                    # last xor on the pivot element
                qrout.apply(
                    qrout_xor,
                    swap_ancillae[swap_ancilla_idx],
                    qregs_rows[i][x],
                    qregs_rows[x][x],
                )
                swap_ancilla_idx += 1

            # improvement 3, X after finishing all phases 1
            qrout.apply(X, qregs_rows[x][x])

        for i in range(r):
            if i == x:
                continue

            _skip_cols_c = skip_cols.copy()
            qrout.apply(X.ctrl(), qregs_rows[i][x], add_ancillae[add_ancilla_idx])
            qrout_xor1 = get_cell_xor(1)
            qrout_xor2 = get_cell_xor(2)
            nxors = 0
            for c in range(n):
                if c not in skip_cols and c != x:
                    ctrl = (
                        add_ancillae[add_ancilla_idx] if nxors % 2 else qregs_rows[i][x]
                    )
                    qrout.apply(qrout_xor2, ctrl, qregs_rows[x][c], qregs_rows[i][c])

            # impr. 2 and 5
            qrout.apply(qrout_xor1, add_ancillae[add_ancilla_idx], qregs_rows[i][x])

            add_ancilla_idx += 1

    return qrout


@build_gate("CELLXOR", [int])
def get_cell_xor(nctrls: int):
    qrout = QRoutine()
    ctrls = qrout.new_wires(nctrls)
    dst = qrout.new_wires(1)
    qrout.apply(X.ctrl(nctrls), ctrls, dst)
    return qrout


@build_gate("ROWSWAP", [int, int, set])
def get_row_swap(n: int, pivot_idx: int, skip_cols: set):
    """WARN: the pivot element is checked agains state 1 (improvement 3)"""
    qrout = QRoutine()
    pivot_row = qrout.new_wires(n)
    other_row = qrout.new_wires(n)
    anc = qrout.new_wires(1)
    qrout.apply(X.ctrl(), pivot_row[pivot_idx], anc)
    qrout_xor = get_cell_xor(2)
    for c in range(n):
        if c not in skip_cols:
            # qrout.apply(X.ctrl(2), anc, other_row[c], pivot_row[c])
            qrout.apply(qrout_xor, anc, other_row[c], pivot_row[c])
        # else:
        #     qrout.apply(FAKE.ctrl(2), anc, other_row[c], pivot_row[c])
    return qrout


@build_gate("ROWADD", [int, int, set])
def get_row_addition(n, pivot_idx: int, skip_cols: set):
    qrout = QRoutine()
    other_row = qrout.new_wires(n)
    pivot_row = qrout.new_wires(n)
    anc = qrout.new_wires(1)
    qrout.apply(X.ctrl(), other_row[pivot_idx], anc)
    qrout_xor1 = get_cell_xor(1)
    qrout_xor2 = get_cell_xor(2)
    for c in range(n):
        if c == pivot_idx:
            # impr. 2
            qrout.apply(qrout_xor1, anc, other_row[c])
        elif c not in skip_cols:
            qrout.apply(qrout_xor2, anc, pivot_row[c], other_row[c])
        # else:
        #     qrout.apply(FAKE.ctrl(2), anc, other_row[c], pivot_row[c])
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
