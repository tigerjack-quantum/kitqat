from numpy import testing as nptesting
from qat.external.utils.qatmgmt.gates import (
    GATE_SET_QAT, get_gate_from_circuit_operation,
    get_np_matrix_from_circuit_operation,
    get_gate_from_circuit_operation)
from qat.lang.AQASM import H, Program, X, Y, RX, RY, RZ

from .common_circuit import CircuitTestCase

# TODO check the get_gate_from_circuit_operation functions and their variables_map parameter


class TestQatmgmtGates(CircuitTestCase):
    def test_get_np_matrix_from_op(self):
        p = Program()
        q = p.qalloc(3)
        p.apply(X, q[0])
        p.apply(H, q[0])
        p.apply(X.ctrl(), q[0], q[1])
        p.apply(H, q[2])
        c = p.to_circ()

        for op in c:
            matrix = get_np_matrix_from_circuit_operation(c, op, {})
            self.assertIsNotNone(matrix)
            nptesting.assert_array_equal(matrix, GATE_SET_QAT[op.gate][1])

    def test_get_np_matrix_from_op_submatrices_only(self):
        p = Program()
        q = p.qalloc(3)
        p.apply(H.ctrl(2), q)
        p.apply(Y.ctrl(), q[0], q[1])
        c = p.to_circ(submatrices_only=True)
        c2 = p.to_circ(submatrices_only=False)
        expected = [{
            'subgate': H,
            'nb_ctrls': 2
        }, {
            'subgate': Y,
            'nb_ctrls': 1
        }]

        for op, op2, expgate in zip(c, c2, expected):
            matrix = get_np_matrix_from_circuit_operation(c, op)
            self.assertIsNotNone(matrix)
            matrix2 = get_np_matrix_from_circuit_operation(c2, op2)
            nptesting.assert_array_equal(matrix, matrix2)
            gate, _ = get_gate_from_circuit_operation(c, op, {})
            self.assertIsNotNone(gate)
            self.assertEqual(gate.subgate, expgate['subgate'])
            self.assertEqual(gate.nb_ctrls, expgate['nb_ctrls'])

    def test_get_gate_from_circuit_operation_param(self):
        p = Program()
        q = p.qalloc(2)
        p.apply(H, q[0])
        p.apply(H, q[1])
        p.apply(RX(1.23), q[0])
        p.apply(RY(2.34).ctrl(), q)
        c = p.to_circ()

        p2 = Program()
        q2 = p2.qalloc(2)
        for op in c.ops:
            g, _ = get_gate_from_circuit_operation(c, op, {})
            p2.apply(g, [q2[i] for i in op.qbits])


        c2 = p2.to_circ()

        res = self.qpu.submit(c.to_job())
        res2 = self.qpu.submit(c2.to_job())
        print(res)
        print(res2)

