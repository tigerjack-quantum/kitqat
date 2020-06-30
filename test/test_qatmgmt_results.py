from numpy import testing as nptesting
from qat.external.utils.qatmgmt.results import (
    get_sample_for_basis_dec_from_res, get_state_vector_from_result)
from qat.lang.AQASM import H, Program, X

from .common_circuit import CircuitTestCase


class TestQatmgmtResults(CircuitTestCase):
    @staticmethod
    def _sample_program():
        p = Program()
        q = p.qalloc(3)
        p.apply(X, q[0])
        p.apply(H, q[0])
        p.apply(X.ctrl(), q[0], q[1])
        p.apply(H, q[2])
        expected_vector = [
            0.5 + 0j, 0.5 + 0j, 0j, 0j, 0j, 0j, -0.5 + 0j, -0.5 + 0j
        ]
        return p, dict(enumerate(expected_vector))
    def test_get_state_vector_from_result(self):
        p, exp_dict = self._sample_program()
        res = self.qpu.submit(p.to_circ().to_job())
        sv = get_state_vector_from_result(res, p.qbit_count)
        nptesting.assert_array_almost_equal(sv, list(exp_dict.values()))

    def test_get_sample_for_basis_state_from_res(self):
        p, exp_dict = self._sample_program()
        res = self.qpu.submit(p.to_circ().to_job())
        for state, value in exp_dict.items():
            with self.subTest(state=state, value=value):
                obtained_value = get_sample_for_basis_dec_from_res(
                    res, state)
                if value == 0:
                    self.assertIsNone(obtained_value)
                else:
                    self.assertAlmostEqual(obtained_value.amplitude, value)
