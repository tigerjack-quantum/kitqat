from typing import List

from qat.lang.AQASM.gates import X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.routines import QRoutine


@build_gate("COND_INIT_A", [List, bool])
def initialize_qureg_given_bitarray(
    a_arr: list,
    little_endian: bool,
) -> QRoutine:
    qr = QRoutine()
    bits = qr.new_wires(len(a_arr))
    print(a_arr)

    mrange = zip(bits, reversed(a_arr)) if little_endian else zip(bits, a_arr)
    for qbit, aint in mrange:
        if aint == 1:
            qr.apply(X, qbit)
        elif aint != 0:
            err_mes = "string %s contains non-binary value %s" % (a_arr, aint)
            raise ValueError(err_mes)
    return qr


@build_gate("MATRIX_INIT", [List])
def initialize_qureg_to_binary_matrix(matrix):
    nrows, ncols = len(matrix), len(matrix[0])
    qfun = QRoutine()
    for row_idx in range(nrows):
        qreg = qfun.new_wires(ncols)
        row = matrix[row_idx]
        qrout = initialize_qureg_given_bitarray(row, False)
        qfun.apply(qrout, qreg)
    return qfun


def export_to_aqasm():
    matrix = [[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]]
    nrows, ncols = len(matrix), len(matrix[0])
    pr = Program()
    qr_mat = pr.qalloc(nrows * ncols)
    qg_mat = initialize_qureg_to_binary_matrix(matrix)
    pr.apply(qg_mat, qr_mat)
    pr.export("rref.aqasm")


def main():
    export_to_aqasm()


if __name__ == '__main__':
    main()
