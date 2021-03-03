import functools
import operator
from test.common_circuit import CircuitTestCase

import numpy as np
from parameterized import parameterized
from qat.external.utils.qroutines import qregs_init, rref
from qat.lang.AQASM.program import Program
from sympy import Matrix


class RrefTestCase(CircuitTestCase):
    def _prepare_circuit(self, matrix):
        self.pr = Program()
        n_rows, n_cols = matrix.shape
        self.qregs_rows = []
        for row_idx in range(n_rows):
            # qregs_rows.append(qregs_init.ini)
            qreg = self.pr.qalloc(n_cols)
            qrout = qregs_init.initialize_qureg_given_bitarray(
                matrix[row_idx, :], qreg, False)
            self.pr.apply(qrout, qreg)
            self.qregs_rows.append(qreg)

        self.qbit_range = set(q.index for qreg in self.qregs_rows
                              for q in qreg)
        self.nsquare = min(matrix.shape)
        self.add_qregs = self.pr.qalloc(self.nsquare * (self.nsquare - 1))
        self.swap_qregs = self.pr.qalloc(int(len(self.add_qregs) / 2))

    @parameterized.expand([
        ("3x3", np.array([[0, 1, 1], [1, 0, 1], [0, 0, 1]]), False),
        # Next one should fail since the first columns contains all 0's
        ("3x3", np.array([[0, 1, 1], [0, 0, 1], [0, 1, 1]]), True),
        ("4x4", np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]]), False),
    ])
    def test_simple(self, name, matrix, should_fail):
        self._prepare_circuit(matrix)

        nrows, ncols = matrix.shape
        rref_gate = rref.get_rref(nrows, ncols)
        self.pr.apply(rref_gate, self.qregs_rows, self.swap_qregs,
                      self.add_qregs)

        measuring = functools.reduce(operator.concat,
                                     [i.qbits for i in self.qregs_rows])
        measuring_idxs = [qb.index for qb in measuring]
        self.pr.measure(qbits=self.swap_qregs)
        self.pr.measure(qbits=self.add_qregs)
        cr = self.pr.to_circ()
        res = self.qpu.submit(cr.to_job(qubits=self.qregs_rows))

        sample = res.raw_data[0]
        mat_rref = rref.build_rref_matrix_from_sample(sample, measuring_idxs,
                                                      matrix.shape)

        mat_rref_sim = Matrix(matrix).rref(pivots=False)
        if should_fail:
            with self.assertRaises(AssertionError):
                np.testing.assert_array_equal(mat_rref, mat_rref_sim)
        else:
            np.testing.assert_array_equal(mat_rref, mat_rref_sim)

        u = rref.build_u_matrix_from_sample(sample, self.nsquare)
        np.testing.assert_array_equal(u @ matrix % 2, mat_rref)
