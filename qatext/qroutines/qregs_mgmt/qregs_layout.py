from qat.lang.AQASM.gates import SWAP, I
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.gates import AbstractGate
from math import floor
from qatext.qroutines.sorting import sorting_network as sn

rotate = AbstractGate("ROT_D", [int, int], arity=lambda n, _: n)
rotate_reg = AbstractGate("ROT_REG_D", [int, int], arity=lambda n, _: n)
reverse = AbstractGate("REVERSE", [int], arity=lambda n: n)

# Rotate alg., check
# https://www.geeksforgeeks.org/program-for-array-rotation-continued-rotate-algorithm/


@build_gate("REVERSE", [int], arity=lambda n: n)
def reverse(nqubits: int) -> QRoutine:
    """Reverse the qubits of a register"""
    mid = int(floor(nqubits / 2))
    qrout = QRoutine()
    if mid <= 0:
        qrout.apply(I, 0)
        return qrout
    for i in range(mid):
        qrout.apply(SWAP, i, nqubits - i - 1)
    return qrout


@build_gate('SWAP_QREG', [int], lambda x: x * 2)
def swap_qreg_cells(n_cell_size):
    """Swaps the matching qubits of two quantum registers having the same size"""
    qf = QRoutine()
    qreg1 = qf.new_wires(n_cell_size)
    qreg2 = qf.new_wires(n_cell_size)
    for cell_bit in range(n_cell_size):
        qf.apply(SWAP, qreg1[cell_bit], qreg2[cell_bit])
    return qf


@build_gate("ROT_D", [int, int], arity=lambda n, _: n)
def rotate(nqubits: int, d: int):
    """Rotate a set of nqbubits by d position. If d is >0, then it's a left
    rotation; if it's < 0, it's a right rotation."""
    qrout = QRoutine()
    wires = qrout.new_wires(nqubits)
    d1 = abs(d) % nqubits
    if d1 == 0 or d1 == nqubits:
        qrout.apply(I, wires[0])
        return qrout
    qrout.apply(reverse(nqubits), wires)
    if d > 0:
        qrout.apply(reverse(d1), wires[nqubits - d1:])
        qrout.apply(reverse(nqubits - d1), wires[:nqubits - d1])
    else:
        qrout.apply(reverse(d1), wires[:d1])
        qrout.apply(reverse(nqubits - d1), wires[d1:])
    return qrout


@build_gate("ROT_REG_D", [int, int, int], arity=lambda n, n2, _: n * n2)
def reg_rotate(nregs: int, qreg_size: int, d: int):
    """Rotate a set of `nregs` register by `d` positions. If d is >0, then it's
 a left rotation; if it's < 0, it's a right rotation. All the registers must be
 of the same size.

    """

    qrout = QRoutine()
    wires = qrout.new_wires(nregs * qreg_size)
    d2 = d * qreg_size

    qrout2 = rotate(len(wires), d2)
    qrout.apply(qrout2, wires)

    return qrout


@build_gate("SWAP_COLS", [int])
def swap_columns(nrows: int):
    routine = QRoutine()
    col1 = routine.new_wires(nrows)
    col2 = routine.new_wires(nrows)

    for wire1, wire2 in zip(col1, col2):
        routine.apply(SWAP, wire1, wire2)

    return routine


@build_gate("SWAP_ROWS", [int])
def swap_rows(ncols: int):
    # TODO
    pass


def move_columns_end_data(nrows: int, ncols: int):
    data = sn.get_pattern_sorter(ncols)
    data["n_rows"] = nrows
    data["n_cols"] = data["n_lines"]
    data["n_cols_orig"] = ncols
    return data


@build_gate("MOVE_COLS_END", [dict])
def move_columns_end_gate(data: dict) -> QRoutine:
    """Use a sorting network to move the columns of the matrix to the end. The
    matrix must be created with the corresponding method from this class,
    otherwise results are undefined.

    :param nrows: number of rows of the original matrix
    :param data: data obtained from :meth: `move_columns_end_data`
    :returns: QRoutine

    The returned QRoutine takes as input:
    #. the original matrix qbits (A), initialized using the
    :meth: `initialize_qureg_to_binary_matrix` function.
    #. a qreg (COMB) of the same length of the matrix columns. The vector should
    contain a 1 for each column that is selected, i.e., for each column that will
    be moved at the end of the matrix
    #. a qreg (COMP) containing the qubits that will be used for the swaps. All qbits
    must be 0.
    """
    ncols: int = data["n_cols"]
    comp_len: int = data["n_comps"]
    nrows: int = data["n_rows"]

    routine = QRoutine()
    row_wires = []
    for _ in range(nrows):
        row_wires.append(routine.new_wires(ncols))
    col_wires = []
    for col_idx in range(ncols):
        col_wires.append(list([qr[col_idx] for qr in row_wires]))

    comb = routine.new_wires(ncols)
    comp = routine.new_wires(comp_len)

    sort_net = sn.build_gate_sorter(data)
    routine.apply(sort_net, comb, comp)

    qrout = swap_columns(nrows)
    for pattern in data["swaps_pattern"]:
        routine.apply(qrout.ctrl(), comp[pattern[0]], col_wires[pattern[1]],
                      col_wires[pattern[2]])
    return routine
