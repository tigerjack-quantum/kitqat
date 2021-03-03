import functools
import operator
import os

import numpy as np
from qat.external.utils.qasm.converters.chp import simulate_chp, to_chp
from qat.external.utils.qroutines import qregs_init, rref
from qat.lang.AQASM.program import Program
from qat.core.console import display
from qat.qpus import LinAlg, Feynman
from qat.external.utils.qatmgmt import results
from qat.core.util import statistics


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
    # TODO it doesn't work if rows > cols
    # Should be ok
    # matrix = np.array([[0, 1, 1], [1, 0, 1], [0, 0, 1]])
    # Should fail
    # matrix = np.array([[0, 1, 1], [0, 0, 1], [0, 1, 1]])
    # Should be long
    # matrix = np.array([[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]])
    # Non square matrix test
    matrix = np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]])
    matrix_list = matrix.tolist()
    pr, qregs_rows, qbit_range = _prepare_circuit(matrix)

    nrows, ncols = matrix.shape
    nsquare = min(nrows, ncols)
    aouts = []
    bouts = []

    # rref_gate = rref.get_rref(nrows, ncols, aouts, bouts)
    # aout_reg = pr.qalloc()
    # pr.apply(rref_gate, qreg_rows)

    # We expect square matrix. U is used to keep track of transformations applied
    for i in range(nsquare):
        if i != nsquare - 1:
            # we don't apply swap gates for the last row
            agate = rref.get_row_swap(nsquare, ncols, i)
            aoutn = len(range(i + 1, nsquare))
            aout = pr.qalloc(aoutn)
            aouts.append(aout)
            print(f"Row {i}")
            print(f"qregs {[j for j in qregs_rows[i]]}")
            pr.apply(agate, *qregs_rows, aout)

        bgate = rref.get_row_addition(nsquare, ncols, i)
        boutn = nsquare - 1
        bout = pr.qalloc(boutn)
        bouts.append(bout)
        pr.apply(bgate, *qregs_rows, bout)
        print(f"Row {i} end")

    cr = pr.to_circ()
    display(cr, max_depth=3)
    print(statistics(cr))
    input("a")
    del cr
    # qbits of matrix
    measuring = functools.reduce(operator.concat,
                                 [i.qbits for i in qregs_rows])
    measuring_idxs = [qb.index for qb in measuring]
    # for qb in aouts:
    aout_meas = functools.reduce(operator.concat, [i.qbits for i in aouts], [])
    if len(aout_meas) > 0:
        pr.measure(qbits=aout_meas)
    bout_meas = functools.reduce(operator.concat, [i.qbits for i in bouts], [])
    # for qb in bouts:
    if len(bout_meas) > 0:
        pr.measure(qbits=bout_meas)

    qpu = LinAlg()
    # qpu = Feynman()
    cr = pr.to_circ()
    print(f"n qubits = {cr.nbqbits}")
    res = qpu.submit(cr.to_job(qubits=qregs_rows))
    sample = res.raw_data[0]
    mat = rref.build_rref_matrix_from_result(res, measuring_idxs, matrix.shape)

    print("original matrix")
    print(matrix)
    print("rref matrix")
    print(mat)
    print("sample")
    print(sample)

    # Reconstruct matrix of transformations u

    # res2 = qpu.submit(cr.to_job(qubits=aouts + bouts))
    # print(res2)
    if len(sample.intermediate_measurements) != 2:
        print(f"we have {len(sample.intermediate_measurements)} intermediate measurements")
        return
    inter_meas_aout, inter_meas_bout = [i.cbits for i in sample.intermediate_measurements]
    swap_idx = 0
    add_idx = 0
    u = np.eye(nsquare, dtype=int)
    for i in range(nsquare):
        for j in range(i + 1, nsquare):
            print(f"swap idx {swap_idx}")
            if inter_meas_aout[swap_idx]:
                u[i, ] += u[j, ]
            swap_idx += 1
        for j in range(nsquare):
            if j == i:
                continue
            print(f"add idx {add_idx}")
            if inter_meas_bout[add_idx]:
                u[j, ] += u[i, ]
            add_idx += 1

    u = u % 2
    print("u matrix")
    print(u)
    print("double check. This ...")
    print(u @ matrix % 2)
    print("... should be equal to this")
    print(mat)

def main():
    test_simple()


if __name__ == '__main__':
    main()
