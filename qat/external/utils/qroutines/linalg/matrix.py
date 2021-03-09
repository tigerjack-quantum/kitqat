from typing import TYPE_CHECKING, Set, Tuple

import nptyping
import numpy as np
from qat.external.utils.qroutines import qregs_init
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

if TYPE_CHECKING:
    from qat.core.wrappers.result import Sample


@build_gate("MATRIX_INIT", [nptyping.NDArray])
def initialize_qureg_to_binary_matrix(matrix):
    """Initialize a set of quregs to the value of the binary matrix, row-wise. I.e.
       matrix [[1, 0], [1, 0]] will produce qreg [1, 0, 1, 0].

    :param matrix: The binary matrix
    :param little_endian:  The endiannes
    :returns: QRoutine

    """
    n_rows, n_cols = matrix.shape
    qfun = QRoutine()
    for row_idx in range(n_rows):
        # qregs_rows.append(qregs_init.ini)
        qreg = qfun.new_wires(n_cols)
        qrout = qregs_init.initialize_qureg_given_bitarray(
            matrix[row_idx, :], False)
        qfun.apply(qrout, qreg)

    return qfun


def get_rows_as_qbit_list(nrows, ncols, qreg):
    rows_qbits = []
    for row_idx in range(nrows):
        rows_qbits.append(list(qreg[row_idx * ncols:row_idx * ncols + ncols]))
    return rows_qbits


def build_matrix_from_sample(sample: 'Sample', qreg_range: Set[int],
                             shape: Tuple[int, int]):
    matrix = np.zeros(shape, dtype=np.ubyte)
    interesting_bits = [
        val for i, val in enumerate(sample.state.bitstring) if i in qreg_range
    ]
    for i, val in enumerate(interesting_bits):
        row = i // shape[1]
        col = i % shape[1]
        matrix[row][col] = val
    return matrix
