from numpy import testing as nptesting
from qat.external.utils.qatmgmt.gates import GATE_SET, get_np_matrix_from_op
from qat.lang.AQASM import H, Program, X

from .common_circuit import CircuitTestCase


class TestQatmgmtGates(CircuitTestCase):
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

    def test_get_np_matrix_from_op(self):
        p, _ = self._sample_program()
        c = p.to_circ()

        for op in c.ops:
            matrix = get_np_matrix_from_op(c, op)
            self.assertIsNotNone(matrix)
            nptesting.assert_array_equal(matrix, GATE_SET[op.gate][1])
