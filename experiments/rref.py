import functools
import operator

import numpy as np
from qat.core.console import display
from qat.core.util import statistics
from qat.external.utils.qroutines import qregs_init, rref
from qat.lang.AQASM.program import Program
from qat.qpus import LinAlg


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


def _rref():
    pass


def _measure_ancillae():
    pass


def test_simple():
    # Should be ok
    # mat = np.array([[0, 1, 1], [1, 0, 1], [0, 0, 1]])
    # Should fail
    # mat = np.array([[0, 1, 1], [0, 0, 1], [0, 1, 1]])
    # Should be long
    # mat = np.array([[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]])
    # Non square mat test
    mat = np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]])
    pr, qregs_rows, qbit_range = _prepare_circuit(mat)

    nrows, ncols = mat.shape
    nsquare = min(nrows, ncols)
    # aouts = []
    # bouts = []

    bout_qregs = pr.qalloc(nsquare * (nsquare - 1))
    aout_qregs = pr.qalloc(int(len(bout_qregs) / 2))
    rref_gate = rref.get_rref(nrows, ncols)
    pr.apply(rref_gate, qregs_rows, aout_qregs, bout_qregs)

    cr = pr.to_circ()
    display(cr, max_depth=3)
    print(statistics(cr))
    del cr
    # qbits of mat
    measuring = functools.reduce(operator.concat,
                                 [i.qbits for i in qregs_rows])
    measuring_idxs = [qb.index for qb in measuring]
    pr.measure(qbits=aout_qregs)
    pr.measure(qbits=bout_qregs)

    qpu = LinAlg()
    # qpu = Feynman()
    cr = pr.to_circ()
    print(f"n qubits = {cr.nbqbits}")
    res = qpu.submit(cr.to_job(qubits=qregs_rows))
    sample = res.raw_data[0]
    print("sample")
    print(sample)

    mat_rref = rref.build_rref_matrix_from_sample(sample, measuring_idxs,
                                                  mat.shape)
    print("original mat")
    print(mat)
    print("rref mat")
    print(mat_rref)

    u = rref.build_u_matrix_from_sample(sample, nsquare)
    print("u mat")
    print(u)
    print("double check: u * mat_original...")
    print(u @ mat % 2)
    print("... should be equal to mat_rref")
    print(mat_rref)


def main():
    test_simple()


if __name__ == '__main__':
    main()
