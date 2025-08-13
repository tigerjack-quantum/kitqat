import unittest
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import RProgram
from test.common_circuit import CircuitTestCase

import numpy as np
from parameterized import parameterized
# from qatext.qroutines.linalg import matrix as qmatrix
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.qatmgmt.sample import build_matrix_from_bitstring, build_u_matrix_from_bitlists
from qatext.qroutines.linalg import rref
from qat.lang.AQASM.program import Program
from sympy import Matrix

# from qat.core.util import statistics


class RrefTestCase(CircuitTestCase):
    def _prepare_circuit(self, matrix):
        self.prw = ProgramWrapper(Program())
        nrows, ncols = matrix.shape
        self.nsquare = min(matrix.shape)
        # qrout = qmatrix.initialize_qureg_to_binary_matrix(matrix.tolist())
        qrout = qi.initialize_qureg_to_binary_matrix(matrix)
        # qr_matrix = self.prw.qalloc(nrows * ncols)
        # self.qregs_rows = qi.get_rows_as_qubit_list(nrows, ncols, qr_matrix)
        self.qmatrix = self.prw.qmatrix_alloc(nrows, ncols, 1, "matrix", str)
        self.prw.apply(qrout, self.qmatrix)

        # self.qbit_range = set(q.index for qreg in self.qregs_rows for q in qreg)
        self.qbit_range = set(range(self.prw._name_to_qarray["matrix"].slic.start,
                                    self.prw._name_to_qarray["matrix"].slic.stop
                                    ))
        swap_anc_n, add_anc_n = rref.get_required_ancillae(nrows, ncols)
        self.swap_qregs = self.prw.qalloc(swap_anc_n)
        self.add_qregs = self.prw.qalloc(add_anc_n)

    def _common_test(self, matrix, test_u=False, test_iden=False, should_fail=False):
        self._prepare_circuit(matrix)

        nrows, ncols = matrix.shape
        rref_gate = rref.get_rref(nrows, ncols)
        self.prw.apply(rref_gate, *self.qmatrix, self.swap_qregs, self.add_qregs)

        cr = self.prw.to_circ()
        tomeasure = [qb for qb in self.qbit_range]
        if test_u:
            tomeasure.extend([qb.index for qb in self.swap_qregs])
            tomeasure.extend([qb.index for qb in self.add_qregs])

        if self.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(cr)
            bitstring = "".join([str(rpr.rbits[idx]) for idx in tomeasure])
        else:
            res = self.qpu.submit(cr.to_job(qubits=tomeasure))

            sample = None
            for sample in res:
                pass
            if sample is None:
                raise Exception("Unknown flow")
            bitstring = sample.state.bitstring
        mat_rref = build_matrix_from_bitstring(
            bitstring, self.qbit_range, matrix.shape
        )
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
                        mat_rref[: self.nsquare, : self.nsquare], np.eye(self.nsquare)
                    )
            else:
                np.testing.assert_array_equal(mat_rref, mat_rref_sim)

        # The matrix of transformations U can be reconstructed from the
        # ancillae.
        if test_u:
            swap_idxs = [qb.index for qb in self.swap_qregs]
            add_idxs = [qb.index for qb in self.add_qregs]
            swap_vals = [int(bitstring[i]) for i in swap_idxs]
            add_vals = [int(bitstring[i]) for i in add_idxs]
            unew = build_u_matrix_from_bitlists(swap_vals, add_vals, self.nsquare)
            # u = build_u_matrix_from_sample(sample, self.nsquare)
            np.testing.assert_array_equal(unew @ matrix % 2, mat_rref)

    @parameterized.expand(
        [
            ("3x3", np.array([[0, 1, 1], [1, 0, 1], [0, 0, 1]])),
            ("3x4", np.array([[1, 1, 0, 0], [1, 0, 0, 0], [0, 1, 1, 1]])),
            ("3x4", np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]])),
        ]
    )
    def test_equals_iden(self, name, matrix):
        # They should give the same results of a normal RREF and an identity matrix on
        # the left
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, True, False)

    @parameterized.expand(
        [
            ("3x5", np.array([[0, 1, 1, 1, 0], [0, 1, 0, 0, 0], [1, 1, 0, 0, 1]])),
        ]
    )
    @unittest.skipUnless(
        CircuitTestCase.SLOW_TEST_ON or CircuitTestCase.REVERSIBLE_ON,
        CircuitTestCase.SLOW_TEST_ON_REASON,
    )
    def test_equals_iden_slow(self, name, matrix):
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, True, False)

    @parameterized.expand(
        [
            ("3x3", np.array([[0, 1, 1], [0, 0, 1], [0, 1, 1]])),
            ("3x4", np.array([[0, 0, 0, 1], [1, 0, 0, 1], [0, 0, 0, 1]])),
        ]
    )
    def test_not_equals_not_iden(self, name, matrix):
        # They should give different w.r.t. a normal RREF, and also no identity
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, True, True)

    @parameterized.expand(
        [("3x5", np.array([[0, 0, 0, 1, 1], [0, 1, 0, 0, 0], [0, 1, 1, 0, 1]]))]
    )
    @unittest.skipUnless(
        CircuitTestCase.SLOW_TEST_ON or CircuitTestCase.REVERSIBLE_ON,
        CircuitTestCase.SLOW_TEST_ON_REASON,
    )
    def test_not_equals_not_iden_slow(self, name, matrix):
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, True, True)

    @parameterized.expand(
        [
            ("3x4", np.array([[1, 1, 1, 0], [1, 1, 1, 0], [1, 0, 0, 0]])),
            ("3x4", np.array([[0, 0, 0, 1], [1, 1, 1, 0], [1, 0, 0, 1]])),
        ]
    )
    def test_equals_not_iden(self, name, matrix):
        # They should give the same results using the reversible circuit
        # w.r.t. the normal RREF, but still no identity
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, False, False)

    @parameterized.expand(
        [
            ("3x5", np.array([[1, 0, 0, 1, 0], [0, 0, 0, 0, 0], [1, 1, 0, 1, 1]])),
        ]
    )
    @unittest.skipUnless(
        CircuitTestCase.SLOW_TEST_ON or CircuitTestCase.REVERSIBLE_ON,
        CircuitTestCase.SLOW_TEST_ON_REASON,
    )
    def test_equals_not_iden_slow(self, name, matrix):
        self.logger.debug("test with %s", name)
        self._common_test(matrix, True, False, False)
