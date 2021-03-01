import functools
import operator
import os

import numpy as np
from qat.external.utils.qasm.converters.chp import simulate_chp, to_chp
from qat.external.utils.qroutines import qregs_init, rref
from qat.external.utils.synthesis.mctrls.mcx import ccnot, x
from qat.lang.AQASM.program import Program


def _prepare_circuit(matrix):
    pr = Program()
    n_rows, n_cols = matrix.shape
    qregs_rows = []
    for row_idx in range(n_rows):
        # qregs_rows.append(qregs_init.ini)
        qreg = pr.qalloc(n_cols)
        qrout = qregs_init.initialize_qureg_given_bitarray(
            matrix[row_idx, :], qreg, False)
        pr.apply(qrout, qreg)
        qregs_rows.append(qreg)

    qbit_range = set(q.index for qreg in qregs_rows for q in qreg)
    return pr, qregs_rows, qbit_range


def test_simple():
    matrix = np.array([[0, 1, 1], [1, 0, 1], [1, 0, 0]])
    matrix_list = matrix.tolist()
    pr, qregs_rows, qbit_range = _prepare_circuit(matrix)

    nrows, ncols = matrix.shape
    for i in range(nrows):
        agate = rref.get_row_swap(matrix_list, i)
        aoutn = len(range(i + 1, nrows))
        boutn = nrows - 1
        aout = pr.qalloc(aoutn)
        bout = pr.qalloc(boutn)
        bgate = rref.get_row_addition(matrix_list, i)
        print(f"Row {i}")
        print(f"qregs {[j for j in qregs_rows[i]]}")
        pr.apply(agate, *qregs_rows, aout)
        pr.apply(bgate, *qregs_rows, bout)
        print(f"Row {i} end")

    measuring = functools.reduce(operator.concat,
                                 [i.qbits for i in qregs_rows])
    measuring_idxs = [qb.index for qb in measuring]
    pr.measure(qbits=measuring)
    # display(self.pr.to_circ(), max_depth=3)
    # res = self.qpu.submit(self.pr.to_circ(link=[get_ccnot]).to_job())
    cr = pr.to_circ(link=[ccnot, x], inline=True)
    cr.dump('./rref.circ')
    # jb = cr.to_job(nbshots=1)
    # jb.dump('./rref.job')
    os.system('circ2aqasm rref.circ')
    to_chp('rref.circ.aqasm', 'rref.chp')
    res = simulate_chp('rref.chp')
    mat = rref.build_rref_matrix_from_result(res, measuring_idxs, matrix.shape)
    print("original matrix")
    print(matrix)
    print("rref matrix")
    print(mat)


def main():
    test_simple()


if __name__ == '__main__':
    main()
