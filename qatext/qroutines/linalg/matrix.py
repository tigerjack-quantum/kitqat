from typing import TYPE_CHECKING, List, Set, Tuple

# import nptyping
import numpy as np
from qatext.qroutines import qregs_init
from qatext.qroutines.sorting import sorting_network as sn
from qat.lang.AQASM.gates import SWAP
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

if TYPE_CHECKING:
    from qat.core.wrappers.result import Sample
    from qat.lang.AQASM.bits import Qbit, QRegister




def get_rows_as_qubit_list(
    nrows: int, ncols: int, qreg: "QRegister"
) -> List[List["Qbit"]]:
    rows_qbits = []
    for row_idx in range(nrows):
        rows_qbits.append(list(qreg[row_idx * ncols : row_idx * ncols + ncols]))
    return rows_qbits


def get_rows_as_index_list(nrows: int, ncols: int, qreg) -> List[List[int]]:
    rows_qbits = []
    for row_idx in range(nrows):
        row = [qb.index for qb in qreg[row_idx * ncols : row_idx * ncols + ncols]]
        rows_qbits.append(row)
    return rows_qbits


def get_columns_as_qubit_list(
    nrows: int, ncols: int, qreg: "QRegister"
) -> List[List["Qbit"]]:
    cols_qbits = []
    for col_idx in range(ncols):
        lis = [qreg[i] for i in range(col_idx, nrows * ncols, ncols)]
        cols_qbits.append(lis)
    return cols_qbits


def get_columns_as_index_list(
    nrows: int, ncols: int, qreg: "QRegister"
) -> List[List[int]]:
    cols_qbits = []
    for col_idx in range(ncols):
        lis = [qreg[i].index for i in range(col_idx, nrows * ncols, ncols)]
        cols_qbits.append(lis)
    return cols_qbits


@build_gate("SWAP_COLS", [int])
def buildg_swap_columns(nrows: int):
    routine = QRoutine()
    col1 = routine.new_wires(nrows)
    col2 = routine.new_wires(nrows)

    for wire1, wire2 in zip(col1, col2):
        routine.apply(SWAP, wire1, wire2)

    return routine


@build_gate("SWAP_ROWS", [int])
def buildg_swap_rows(ncols: int):
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

    qrout = buildg_swap_columns(nrows)
    for pattern in data["swaps_pattern"]:
        routine.apply(
            qrout.ctrl(), comp[pattern[0]], col_wires[pattern[1]], col_wires[pattern[2]]
        )
    return routine
