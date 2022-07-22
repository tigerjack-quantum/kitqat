"""This gauss-jordan procedure is specifically tailored for ISD
"""
import logging
from functools import partial

from qat.lang.AQASM.gates import CCNOT, CNOT, X, SWAP
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

LOGGER = logging.getLogger(__name__)
# Just a fake swap for pictorial representation of deleted gates
# FAKE = H


def get_required_ancillae(r: int):
    """Get the number of additional (swap_ancilla, add_ancilla) qubits required for
the RREF.

    :param nrows: Rows of matrix
    :returns: (swap_ancilla, add_ancilla)

    """
    add_ancilla_n = r * (r - 1)
    # Add ancilla is necessary an even number, so there is no actual rounding here
    swap_ancilla_n = add_ancilla_n // 2
    return swap_ancilla_n, add_ancilla_n


@build_gate('GJISD', [int, int, bool, int])
def get_rref(r, n, skip_rightmost, norig):
    """Apply RREF to a matrix H.

    :param r: The number of rows of the original matrix H
    :param n: The number of cols of the original matrix H
    :param skip_rightmost: Skip the operations on the rightmost r*k submatrix (used in Prange)
    :param norig is the number of columns of original matrix. In theory, param n can be composed by the original matrix plus the syndrome columns.
    The gate takes as input, in this order:
    - The matrix (r * n), represented as qreg
    - The swap ancillae
    - The add ancillae

    The number of swap and add ancillae required can be obtained through the
    get_ancillae function.

    WARN: if you pass the syndrome(s) as well as columns of the matrix, you
    should put them at the end of the original matrix (i.e., after column n-1)

    """
    qrout = QRoutine()
    # it's the basic algorithm, we need measures for depth
    skip_rightmost = False
    if norig < 0:
        norig = n

    qregs_rows = []
    for _ in range(r):
        qreg = qrout.new_wires(n)
        qregs_rows.append(qreg)

    swap_ancilla_n, add_ancilla_n = get_required_ancillae(r)
    swap_ancillae = qrout.new_wires(swap_ancilla_n)
    add_ancillae = qrout.new_wires(add_ancilla_n)
    add_ancilla_idx = 0
    swap_ancilla_idx = 0

    # impr. 7, we skip the first r columns, but only for the rows above pivot
    # skip_cols_add = set(range(1, r))

    for x in range(r):
        rowswap = partial(get_row_swap, r, n, x)
        rowadd = partial(get_row_addition, r, n, x)
        # we don't apply swap gates for the last row
        if x != r - 1:
            for i in range(x + 1, r):
                qrout.apply(X, qregs_rows[x][x])
                qrout.apply(rowswap(), qregs_rows[x], qregs_rows[i],
                            swap_ancillae[swap_ancilla_idx])
                qrout.apply(X, qregs_rows[x][x])
                swap_ancilla_idx += 1

        # phase 2, put 0 in pivot column for each row below and above pivot one
        for i in range(r):
            # obv, we skip the row under analysis
            if i == x:
                continue
            qrout.apply(rowadd(), qregs_rows[i], qregs_rows[x],
                        add_ancillae[add_ancilla_idx])
            add_ancilla_idx += 1
    return qrout


@build_gate('ROWSWAP', [int, int, int])
def get_row_swap(r: int, n: int, pivot_idx: int):
    """WARN: the pivot element is checked against state 1 (improvement 4)
    r, n: ISD params
    pivot_idx: index of pivot under analysis (in the matrix, it has position M_{pivot_idx, pivot_idx})
    """
    qrout = QRoutine()
    pivot_row = qrout.new_wires(n)
    other_row = qrout.new_wires(n)
    anc = qrout.new_wires(1)
    qrout.apply(CNOT, pivot_row[pivot_idx], anc)

    # we do the first rs, then (if pivot last as per impr. 5) we do pivot, then last ks
    for c in range(n):
        qrout.apply(SWAP.ctrl(), anc, other_row[c], pivot_row[c])
    return qrout


@build_gate('ROWADD', [int, int, int])
def get_row_addition(r: int, n: int, pivot_idx: int):
    """
    r, n: ISD params
    pivot_idx: index of pivot under analysis (in the matrix, it has position M_{pivot_idx, pivot_idx})
    skip_cols: indexes of columns to skip
    pivot_last: if true, pivot element swap will be performed after the other r elements of the matrix, but before the last ks (improvement 6)
    """

    qrout = QRoutine()
    other_row = qrout.new_wires(n)
    pivot_row = qrout.new_wires(n)
    anc = qrout.new_wires(1)
    qrout.apply(CNOT, other_row[pivot_idx], anc)
    for c in range(n):
        qrout.apply(CCNOT, anc, pivot_row[c], other_row[c])
    return qrout
