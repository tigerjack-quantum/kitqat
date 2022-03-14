import unittest
from test.common_circuit import CircuitTestCase

import numpy as np
from parameterized import parameterized
from qat.external.utils.qroutines.linalg import gauss_jordan_isd as gji
from qat.external.utils.qroutines.linalg import matrix as qmatrix
from qat.external.utils.qroutines.linalg import rref
from qat.lang.AQASM.program import Program
from sympy import Matrix


class GjiTestCase(CircuitTestCase):

    def _prepare_circuit(self, matrix):
        pr = Program()
        nrows, ncols = matrix.shape

        qrout = qmatrix.initialize_qureg_to_binary_matrix(matrix)
        qr_matrix = pr.qalloc(nrows * ncols)
        pr.apply(qrout, qr_matrix)
        qregs_rows = qmatrix.get_rows_as_qubit_list(nrows, ncols, qr_matrix)

        qbit_range = set(q.index for qreg in qregs_rows for q in qreg)
        swap_anc_n, add_anc_n = gji.get_required_ancillae(nrows)
        add_qregs = pr.qalloc(add_anc_n)
        swap_qregs = pr.qalloc(swap_anc_n)
        return pr, qregs_rows, add_qregs, swap_qregs, qbit_range

    def _common_test(
        self,
        matrix,
        test_u,
        should_iden,
    ):
        """:param test_u: build u from ancillae and check it's correct
        :param should_iden: we are checking that the procedure gives an identity matrix. Note that, if skip_rightmost is true, we do not have exactly an identity matrix, but still the diagonal elements are all 1 and the bottom-left submatrix below the diagonal is all zero
        """
        r, n = matrix.shape
        nrows = r
        syndrome = np.random.randint(0, 2, size=(nrows, 1))
        ncols = n + 1
        # concatenate the syndrome to the original matrix
        matrix_ext = np.hstack((matrix, syndrome))

        for skip_rightmost in (False, ):
            with self.subTest(skip_rightmost=skip_rightmost):
                pr, qregs_rows, add_qregs, swap_qregs, qbit_range = self._prepare_circuit(
                    matrix_ext)
                gji_gate = gji.get_rref(nrows, ncols, skip_rightmost,
                                        ncols - 1)
                pr.apply(gji_gate, qregs_rows, swap_qregs, add_qregs)

                if test_u:
                    pr.measure(qbits=swap_qregs)
                    pr.measure(qbits=add_qregs)
                cr = pr.to_circ()
                res = self.qpu.submit(cr.to_job(qubits=qbit_range))

                self.assertEqual(len(res), 1)
                sample = res[0]
                mat_gji = qmatrix.build_matrix_from_sample(
                    sample, qbit_range, (nrows, ncols))
                mat_gji_diag = mat_gji.diagonal()
                mat_gji_sim = Matrix(matrix_ext).rref(pivots=False) % 2
                mat_gji_sim_diag = mat_gji_sim.diagonal()
                self.logger.debug(f"skip {skip_rightmost}")
                self.logger.debug("original matrix (last column is syndrome)")
                self.logger.debug(f"\n{matrix_ext}")
                self.logger.debug("reduced matrix from qcircuit")
                self.logger.debug(f"\n{mat_gji}")
                if should_iden:
                    # check we have all ones on the diagonal
                    self.assertTrue(all(mat_gji_diag))
                    self.assertTrue(all(mat_gji_sim_diag))
                    # check the syndrome calculation is correct
                    syn = mat_gji[:, n].reshape(r, 1)
                    np.testing.assert_array_equal(syn, mat_gji_sim[:, n])
                    if not skip_rightmost:
                        # if we didn't skip anything, the results should be identical
                        np.testing.assert_array_equal(mat_gji[:,:r], np.eye(r))
                        np.testing.assert_array_equal(mat_gji, mat_gji_sim)
                    # check as well that we can reconstruct the matrix U s.t. U @ matrix = matrix_reduced
                    if test_u:
                        u = rref.build_u_matrix_from_sample(sample, r)
                        if not skip_rightmost:
                            check_matrix = matrix_ext
                            check_against = mat_gji
                        else:
                            # if we skipped the righmost rxn matrix, we should
                            # check only the leftmost one AND the syndrome
                            range_cols = list(range(r))
                            # append syndrome
                            range_cols.append(n)
                            check_matrix = matrix_ext[:, range_cols]
                            check_against = mat_gji[:, range_cols]
                        np.testing.assert_array_equal(u @ check_matrix % 2,
                                                      check_against)
                else:
                    # in this case, we just check that at least one element on
                    # the diagonal is 0. This is enough to make the algorithm
                    # fail in our isd circuits
                    self.assertFalse(all(mat_gji_diag))
                    self.assertFalse(all(mat_gji_sim_diag))

    @parameterized.expand([
        ("3x3", np.array([[0, 1, 1], [1, 0, 1], [0, 0, 1]])),
        ("3x4", np.array([[1, 1, 0, 0], [1, 0, 0, 0], [0, 1, 1, 1]])),
        ("3x4", np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]])),
    ])
    def test_iden(self, name, matrix):
        """They should give the same results of a normal GJI and an identity matrix on
        the left

        """
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, True)

    @parameterized.expand([
        ("3x3", np.array([[0, 1, 1], [0, 0, 1], [0, 1, 1]])),
        ("3x4", np.array([[0, 0, 0, 1], [1, 0, 0, 1], [0, 0, 0, 1]])),
        ("3x4", np.array([[1, 1, 1, 0], [1, 1, 1, 0], [1, 0, 0, 0]])),
        ("3x4", np.array([[0, 0, 0, 1], [1, 1, 1, 0], [1, 0, 0, 1]])),
    ])
    def test_no_iden(self, name, matrix):
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, False)

    @parameterized.expand([
        ("3x5", np.array([[0, 1, 1, 1, 0], [0, 1, 0, 0, 0], [1, 1, 0, 0, 1]])),
    ])
    @unittest.skipUnless(CircuitTestCase.SLOW_TEST_ON,
                         CircuitTestCase.SLOW_TEST_ON_REASON)
    def test_iden_slow(self, name, matrix):
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, True)

    @parameterized.expand([
        ("3x5", np.array([[0, 0, 0, 1, 1], [0, 1, 0, 0, 0], [0, 1, 1, 0, 1]])),
        ("3x5", np.array([[1, 0, 0, 1, 0], [0, 0, 0, 0, 0], [1, 1, 0, 1, 1]])),
    ])
    @unittest.skipUnless(CircuitTestCase.SLOW_TEST_ON,
                         CircuitTestCase.SLOW_TEST_ON_REASON)
    def test_no_iden_slow(self, name, matrix):
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, False)
