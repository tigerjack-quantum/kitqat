from numpy import testing as nptesting
from qatext.utils.qatmgmt.gates import (
    GATE_SET_QAT,
    from_circuit_to_program,
    generate_gate_from_circuit_op,
    generate_np_matrix_from_circuit_by_op,
)
from qat.lang.AQASM.gates import CNOT, H, X, Y
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.routines import QRoutine

from .common_circuit import CircuitTestCase


# TODO check the generate_gate_from_circuit_op functions and their variables_map parameter
@build_gate("MY_GATE", [int], lambda x: x)
def _m_gate(nbits: int) -> QRoutine:
    qrout = QRoutine()
    qw = qrout.new_wires(nbits)
    for wire in qw[1:]:
        qrout.apply(CNOT, qw[0], wire)
    return qrout


@build_gate("MY_GATE2", [int], lambda x: x)
def _m_gate2(nbits: int) -> QRoutine:
    qrout = QRoutine()
    qw = qrout.new_wires(nbits)
    for wire in qw[1:]:
        qrout.apply(CNOT, qw[0], wire)
    qrout2 = _m_gate(nbits)
    qrout.apply(qrout2, qw)
    return qrout


class TestQatmgmtGates(CircuitTestCase):
    def test_generate_np_matrix_from_op(self):
        p = Program()
        q = p.qalloc(3)
        p.apply(X, q[0])
        p.apply(H, q[0])
        p.apply(X.ctrl(), q[0], q[1])
        p.apply(H, q[2])
        c = p.to_circ()

        for op in c:
            matrix = generate_np_matrix_from_circuit_by_op(c, op, {})
            self.assertIsNotNone(matrix)
            nptesting.assert_array_equal(
                matrix, GATE_SET_QAT[op.gate].matrix_generator()
            )

    def test_generate_np_matrix_from_op_submatrices_only(self):
        p = Program()
        q = p.qalloc(3)
        p.apply(H.ctrl(2), q)
        p.apply(Y.ctrl(), q[0], q[1])
        c = p.to_circ(submatrices_only=True)
        c2 = p.to_circ(submatrices_only=False)
        expected = [{"subgate": H, "nb_ctrls": 2}, {"subgate": Y, "nb_ctrls": 1}]

        for op, op2, expgate in zip(c, c2, expected):
            matrix = generate_np_matrix_from_circuit_by_op(c, op, {})
            self.assertIsNotNone(matrix)
            matrix2 = generate_np_matrix_from_circuit_by_op(c2, op2, {})
            nptesting.assert_array_equal(matrix, matrix2)
            gate, _ = generate_gate_from_circuit_op(c, op, {})
            self.assertIsNotNone(gate)
            self.assertEqual(gate.subgate, expgate["subgate"])
            self.assertEqual(gate.nb_ctrls, expgate["nb_ctrls"])

    def test_circuit_conversion_with_param(self):
        p = Program()
        q = p.qalloc(2)
        p.apply(H, q[0])
        p.apply(H, q[1])
        # p.apply(RX(1.23), q[0])
        # p.apply(RY(2.34).ctrl(), q)
        c = p.to_circ()

        p2 = from_circuit_to_program(c)
        c2 = p2.to_circ()
        res = self.qpu.submit(c.to_job())
        res2 = self.qpu.submit(c2.to_job())

        self.assertEqual(
            [(sample.state.state, sample._amplitude) for sample in res],
            [(sample.state.state, sample._amplitude) for sample in res2],
        )

    def test_circuit_conversion_with_qrout(self):
        p = Program()
        q = p.qalloc(2)
        qrout = QRoutine()
        qrout.apply(H, 0)
        qrout.apply(CNOT, 1, 0)
        p.apply(qrout, q)
        c = p.to_circ()
        res = self.qpu.submit(c.to_job())

        p2 = from_circuit_to_program(c)
        c2 = p2.to_circ()
        res2 = self.qpu.submit(c2.to_job())

        self.assertEqual(
            [(sample.state.state, sample._amplitude) for sample in res],
            [(sample.state.state, sample._amplitude) for sample in res2],
        )

    def test_circuit_conversion_with_buildgate(self):
        p = Program()
        q = p.qalloc(3)
        qrout = _m_gate(3)
        qrout(q)
        c = p.to_circ()
        res = self.qpu.submit(c.to_job())

        p2 = from_circuit_to_program(c)
        c2 = p2.to_circ()
        res2 = self.qpu.submit(c2.to_job())

        self.assertEqual(
            [(sample.state.state, sample._amplitude) for sample in res],
            [(sample.state.state, sample._amplitude) for sample in res2],
        )

    def test_circuit_conversion_with_buildgate_rec(self):
        p = Program()
        q = p.qalloc(3)
        qrout = _m_gate2(3)
        qrout(q)
        c = p.to_circ()
        res = self.qpu.submit(c.to_job())

        p2 = from_circuit_to_program(c)
        c2 = p2.to_circ()
        res2 = self.qpu.submit(c2.to_job())

        self.assertEqual(
            [(sample.state.state, sample._amplitude) for sample in res],
            [(sample.state.state, sample._amplitude) for sample in res2],
        )
