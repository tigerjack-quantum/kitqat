from typing import TYPE_CHECKING, List
from numpy.testing._private.utils import print_assert_equal

from qat.lang.AQASM.gates import X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

# TODO: Ideas
# 1. Use sum to first non 0 element instead of swap rows
# 2. Avoid additional ancillae
#    - In the swap stage, do not take care of the pivot cell: it'll always be 1 at the end. We can just use Use additional `n` qubits initialized to 1. The pivot cell are still necessary as controllers for all the row operations.
#    - In the same way, when adding the pivot row to all the other rows (in order to put all 0's above and below)


# @build_gate("RowSwap", [int, int, int, List])
@build_gate('ROWSWAP', [List, int])
def get_row_swap(matrix: List[List[int]], row_src_idx: int):
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
    qfun = QRoutine()
    nrows, ncols = len(matrix), len(matrix[0])
    print(f"nrows {nrows}, ncols {ncols}")

    # This will contain the source row
    # row_src = qfun.new_wires(row_length)
    row_wires = []
    for _ in range(nrows):
        row_wires.append(qfun.new_wires(ncols))

    col_src_idx = row_src_idx
    print(f"row_src_idx {row_src_idx}")
    row_src = row_wires[row_src_idx]
    print(f"row src {row_src}")
    print(f"row src idxs {[q.index for q in row_src]}")
    for row_oth_idx in range(row_src_idx + 1, nrows):
        # All the possible rows after the source row
        print(f"row_oth_idx {row_oth_idx}")
        row_oth = row_wires[row_oth_idx]
        print(f"row oth {row_oth}")
        print(f"row oth idxs {[q.index for q in row_oth]}")
        # Ancilla telling if the column must be swapped; since it's not reset to 0, I can't add it to the ancillae list
        anc = qfun.new_wires(1)
        # qfun.set_ancillae(anc)
        # print(f"ancillae {qfun.ancillae}")
        print(f"current ancilla {anc}")
        print(f"current ancilla idx {anc[0].index}")
        # CNOT where ctrl must be 0
        # row_src[col_idx] can be 1 in two cases:
        # - It has been set to 1 in the previous round following a swap
        # - It was already 1 to start with
        print(f"X src {row_src[row_src_idx]} ")
        qfun.apply(X, row_src[col_src_idx])
        print(f"CNOT {row_src[col_src_idx]} -> {anc} ")
        qfun.apply(X.ctrl(), row_src[col_src_idx], anc)
        print(f"X src {row_src[col_src_idx]} ")
        qfun.apply(X, row_src[col_src_idx])

        # sum if ancilla is set, but only the col_idxs after the given one. The
        # idea is that all previous idx are already at 0 bcz of previous row
        # operations.
        for col_idx in range(col_src_idx, ncols):
            print(f"CCNOT {anc}, {row_oth[col_idx]} -> {row_src[col_idx]} ")
            qfun.apply(X.ctrl(2), anc, row_oth[col_idx], row_src[col_idx])

    print("----")
    return qfun


@build_gate('ROWADD', [List, int])
def get_row_addition(matrix: List[List[int]], row_src_idx: int):
    qfun = QRoutine()
    nrows, ncols = len(matrix), len(matrix[0])
    print(f"nrows {nrows}, ncols {ncols}")

    # This will contain the source row
    # row_src = qfun.new_wires(row_length)
    row_wires = []
    for _ in range(nrows):
        row_wires.append(qfun.new_wires(ncols))

    col_src_idx = row_src_idx
    print(f"row_src_idx {row_src_idx}")
    row_src = row_wires[row_src_idx]
    print(f"row src {row_src}")
    print(f"row src idxs {[q.index for q in row_src]}")
    # WIP diff, range
    for row_oth_idx in range(nrows):
        if row_oth_idx == row_src_idx:
            continue
        # All the possible rows after the source row
        print(f"row_oth_idx {row_oth_idx}")
        row_oth = row_wires[row_oth_idx]
        print(f"row oth {row_oth}")
        print(f"row oth idxs {[q.index for q in row_oth]}")
        # Ancilla telling if the column must be swapped
        anc = qfun.new_wires(1)
        # qfun.set_ancillae(anc)
        # print(f"ancillae {qfun.ancillae}")
        print(f"current ancilla {anc}")
        print(f"current ancilla idx {anc[0].index}")
        # CNOT where ctrl must be 0
        # row_src[col_idx] can be 1 in two cases:
        # - It has been set to 1 in the previous round following a swap
        # - It was already 1 to start with
        print(f"CNOT {row_src[col_src_idx]} -> {anc} ")
        qfun.apply(X.ctrl(), row_oth[col_src_idx], anc)

        # sum if ancilla is set, but only the col_idxs after the given one. The
        # idea is that all previous idx are already at 0 bcz of previous row
        # operations.
        # WIP, diff, CCNOT src and tgt
        for col_idx in range(col_src_idx, ncols):
            print(f"CCNOT {anc}, {row_oth[col_idx]} -> {row_src[col_idx]} ")
            qfun.apply(X.ctrl(2), anc, row_src[col_idx], row_oth[col_idx])

    print("----")
    return qfun
