from qat.external.utils.qroutines import qregs_init
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate

from typing import Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from qat.core.wrappers.result import Sample

import numpy as np


@build_gate("MATRIX_INIT", [list, bool])
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

    return QRoutine


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
