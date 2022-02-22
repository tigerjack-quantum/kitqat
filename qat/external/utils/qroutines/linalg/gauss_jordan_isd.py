"""This gauss-jordan procedure is specifically tailored for ISD
"""
import logging

from qat.lang.AQASM.gates import X, CNOT, CCNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

LOGGER = logging.getLogger(__name__)
# Just a fake swap for pictorial representation of deleted gates
# FAKE = H


def get_required_ancillae(r: int):
    """Get the number of additional (swap_ancilla, add_ancilla) qubits required for
the RREF.

    :param nrows: Rows of matrix
    :param ncols: Cols of matrix
    :returns: (swap_ancilla, add_ancilla)

    """
    add_ancilla_n = r * (r - 1)
    # Add ancilla is necessary an even number, so there is no actual rounding here
    swap_ancilla_n = add_ancilla_n // 2
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

    for x in range(r):
        # impr. 1
        if x > 0:
            skip_cols.add(x - 1)
        rowadd = get_row_addition(n, x, skip_cols.copy())
        # we don't apply swap gates for the last row
        if x != r - 1:
            # improvement 3, X before starting all phases 1
            qrout.apply(X, qregs_rows[x][x])
            for i in range(x + 1, r):
                if i == r - 1:
                    # before_cols = {x+2}
                    last_cols = {x}
                else:
                    # before_cols = set()
                    last_cols = set()
                rowswap = get_row_swap(n, x, skip_cols.copy(), last_cols)

                qrout.apply(rowswap, qregs_rows[x], qregs_rows[i],
                            swap_ancillae[swap_ancilla_idx])
                swap_ancilla_idx += 1
            # improvement 3, X after finishing all phases 1
            qrout.apply(X, qregs_rows[x][x])

        for i in range(r):
            if i == x:
                continue
            qrout.apply(rowadd, qregs_rows[i], qregs_rows[x],
                        add_ancillae[add_ancilla_idx])
            add_ancilla_idx += 1

    return qrout


@build_gate('ROWSWAP', [int, int, set, set])
def get_row_swap(n: int, pivot_idx: int, skip_cols: set, last_cols: set):
    """WARN: the pivot element is checked agains state 1 (improvement 3)
    """
    qrout = QRoutine()
    pivot_row = qrout.new_wires(n)
    other_row = qrout.new_wires(n)
    anc = qrout.new_wires(1)
    qrout.apply(CNOT, pivot_row[pivot_idx], anc)

    for c in range(n):
        if c not in skip_cols and c not in last_cols:
            qrout.apply(CCNOT, anc, other_row[c], pivot_row[c])
    # impr. 6
    for c in last_cols:
        qrout.apply(CCNOT, anc, other_row[c], pivot_row[c])
    return qrout


@build_gate('ROWADD', [int, int, set])
def get_row_addition(n, pivot_idx: int, skip_cols: set):
    qrout = QRoutine()
    other_row = qrout.new_wires(n)
    pivot_row = qrout.new_wires(n)
    anc = qrout.new_wires(1)
    qrout.apply(CNOT, other_row[pivot_idx], anc)
    for c in range(n):
        if c == pivot_idx:
            # impr. 6
            continue

        elif c not in skip_cols:
            qrout.apply(CCNOT, anc, pivot_row[c], other_row[c])
    
    # impr. 6 + 2
    qrout.apply(CNOT, anc, other_row[pivot_idx])
    return qrout
