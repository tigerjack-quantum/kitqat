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

    def _common_test(self,
                     matrix,
                     test_u=False,
                     test_iden=False,
                     should_fail=False):
        self._prepare_circuit(matrix)

        nrows, ncols = matrix.shape
        rref_gate = rref.get_rref(nrows, ncols)
        self.pr.apply(rref_gate, self.qregs_rows, self.swap_qregs,
                      self.add_qregs)

        # measuring = functools.reduce(operator.concat,
        #                              [i.qbits for i in self.qregs_rows])
        # measuring_idxs = [qb.index for qb in self.qregs_rows]
        if test_u:
            # It doesn't work on myqlm
            self.pr.measure(qbits=self.swap_qregs)
            self.pr.measure(qbits=self.add_qregs)
        cr = self.pr.to_circ()
        res = self.qpu.submit(cr.to_job(qubits=self.qregs_rows))

        sample = res.raw_data[0]
        mat_rref = rref.build_rref_matrix_from_sample(sample, self.qbit_range,
                                                      matrix.shape)
        # input(mat_rref)

        mat_rref_sim = Matrix(matrix).rref(pivots=False)
        # The rrefs are expected to be different
        if should_fail:
            with self.assertRaises(AssertionError):
                np.testing.assert_array_equal(mat_rref, mat_rref_sim)
        else:
            np.testing.assert_array_equal(mat_rref, mat_rref_sim)

        # The rrefs are not necessarily different, but for sure the obtained
        # rref has not an IDENTITY matrix in the left part
        if test_iden:
            if should_fail:
                with self.assertRaises(AssertionError):
                    np.testing.assert_array_equal(
                        mat_rref[:self.nsquare, :self.nsquare],
                        np.eye(self.nsquare))
            else:
                np.testing.assert_array_equal(mat_rref, mat_rref_sim)

        # The matrix of transformations U can be reconstructed from the
        # ancillae. However, it doesn't work properly on myqlm, while it works
        # on QLM 1.0.
        if test_u:
            u = rref.build_u_matrix_from_sample(sample, self.nsquare)
            np.testing.assert_array_equal(u @ matrix % 2, mat_rref)

    @parameterized.expand([
        ("3x3", np.array([[0, 1, 1], [1, 0, 1], [0, 0, 1]])),
        ("3x4", np.array([[1, 1, 0, 0], [1, 0, 0, 0], [0, 1, 1, 1]])),
        ("3x4", np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]])),
        ("3x5", np.array([[0, 1, 1, 1, 0], [0, 1, 0, 0, 0], [1, 1, 0, 0, 1]])),
    ])
    def test_equals_iden(self, name, matrix):
        """They should give the same results of a normal RREF and an identity matrix on
        the left

        """
        self._common_test(matrix, False, True, False)

    @parameterized.expand([
        ("3x3", np.array([[0, 1, 1], [0, 0, 1], [0, 1, 1]])),
        ("3x4", np.array([[0, 0, 0, 1], [1, 0, 0, 1], [0, 0, 0, 1]])),
        ("3x5", np.array([[0, 0, 0, 1, 1], [0, 1, 0, 0, 0], [0, 1, 1, 0, 1]]))
    ])
    def test_not_equals_not_iden(self, name, matrix):
        """They should give different w.r.t. a normal RREF, and also no identity
        """
        self._common_test(matrix, False, True, True)

    @parameterized.expand([
        ("3x4", np.array([[1, 1, 1, 0], [1, 1, 1, 0], [1, 0, 0, 0]])),
        ("3x4", np.array([[0, 0, 0, 1], [1, 1, 1, 0], [1, 0, 0, 1]])),
        ("3x5", np.array([[1, 0, 0, 1, 0], [0, 0, 0, 0, 0], [1, 1, 0, 1, 1]])),
    ])
    def test_equals_not_iden(self, name, matrix):
        """They should give the same results using the reversible circuit
        w.r.t. the normal RREF, but still no identity

        """
        self._common_test(matrix, False, False, False)
