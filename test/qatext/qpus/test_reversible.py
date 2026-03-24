import functools
from test.common_circuit import CircuitTestCase

from qatext.qpus.reversible import RGate, RProgram
from qat.lang.AQASM.gates import CCNOT, SWAP, H, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.routines import QRoutine


@build_gate("MGATE1", [int], lambda x: x)
def _m_gate1(nbits: int) -> QRoutine:
    assert nbits > 1, f"{nbits}"
    qrout = QRoutine()
    qw = qrout.new_wires(nbits)
    for wire in qw[1:]:
        qrout.apply(X.ctrl(1), qw[0], wire)
    return qrout


@build_gate("MGATE2", [int], lambda x: x)
def _m_gate2(nbits: int) -> QRoutine:
    assert nbits > 3
    qrout = QRoutine()
    qw = qrout.new_wires(nbits)
    for i in range(1, len(qw) - 1):
        qrout.apply(SWAP.ctrl(), qw[0], qw[i], qw[i + 1])
    qrout2 = _m_gate1(nbits - 2)
    qrout.apply(qrout2, qw[0], qw[2], qw[4:])
    return qrout


def _m_gate3(nbits: int) -> QRoutine:
    assert nbits > 3
    qrout = QRoutine()
    qw = qrout.new_wires(nbits)
    for i in range(1, len(qw) - 1):
        qrout.apply(SWAP.ctrl(), qw[0], qw[i], qw[i + 1])
    # to access the qroutine itself (and not the abstract/param gate generated
    # through the build gate), we need to use ~
    # qrout2 = (~_m_gate1)(nbits - 2)
    # SAME of tilde operator (line above), but does not interfere with LSP
    qrout2 = _m_gate1.circuit_generator(nbits - 2)
    qrout.apply(qrout2, qw[0], qw[2], qw[4:])
    return qrout


class TestRProgram(CircuitTestCase):
    nrbits = 10

    def setUp(self):
        super().setUp()
        self.rcr = RProgram()
        self.rcr.ralloc(self.nrbits)
        self._test_arr = ["0"] * self.nrbits

    def test_not(self):
        self.rcr.apply(RGate.NOT, 1)
        self._test_arr[1] = "1"
        self.assertEqual(self.rcr.rbits.to01(), "".join(self._test_arr))

    def test_swap(self):
        self.rcr.apply(RGate.NOT, 3)
        self.rcr.apply(RGate.SWAP, 3, 2)
        self._test_arr[2] = "1"
        self.assertEqual(self.rcr.rbits.to01(), "".join(self._test_arr))

    def test_not_disjoints(self):
        self.rcr.rbits.invert(3)
        self.rcr.rbits.invert(4)
        part = functools.partial(self.rcr.apply, RGate.NOT, 4, 4)
        self.assertRaises(ValueError, part)

    def test_mcmnot(self):
        trgts = {1, 3, 4, 9}
        ctrls = {2, 5}
        for i in ctrls:
            self.rcr.rbits.invert(i)
            self._test_arr[i] = "1"
        for i in trgts:
            self._test_arr[i] = "1"
            self.rcr.apply(RGate.NOT, *ctrls, i)
        self.assertEqual(self.rcr.rbits.to01(), "".join(self._test_arr))

    def test_program_to_rprogram_error(self):
        pr = Program()
        pr.apply(H, pr.qalloc(1))

        circ = pr.to_circ()
        rpr = RProgram.circuit_to_rprogram(circ)
        part = functools.partial(rpr.apply_gates_from_circuit, circ, circ)
        self.assertRaises(AttributeError, part)

    def test_qcircuit_to_rprogram_with_controlled(self):
        progC = Program()
        qr = progC.qalloc(4)
        progC.apply(X, qr[0])
        progC.apply(X, qr[1])
        progC.apply(X, qr[2])
        progC.apply(CCNOT.ctrl(1), qr)
        circC = progC.to_circ()
        res = self.qpu.submit(circC.to_job())
        sample = None
        for sample in res:
            pass
        assert sample is not None
        rpr = RProgram.circuit_to_rprogram(circC)
        rpr.apply_gates_from_circuit(circC, circC)
        self.assertEqual(sample.state.bitstring, rpr.rbits.to01())



    def test_qcircuit_to_rprogram_with_custom_gates(self):
        pr = Program()
        qr = pr.qalloc(5)
        pr.apply(X, qr[0])
        pr.apply(X, qr[4])
        pr.apply(SWAP, qr[4], qr[3])
        # pr.apply(CNOT, qr[:2])
        pr.apply(X.ctrl(), qr[0], qr[1])
        pr.apply(CCNOT, qr[:3])
        pr.apply(SWAP, qr[2], qr[4])
        pr.apply(SWAP.ctrl(3), qr)
        # Note that this last 2 gates are not applied since their ctrls are not all 1's
        pr.apply(CCNOT, qr[2:5])
        pr.apply(SWAP.ctrl(3), qr)
        cr = pr.to_circ()
        res = self.qpu.submit(cr.to_job())
        sample = None
        for sample in res:
            pass
        assert sample is not None
        rpr = RProgram.circuit_to_rprogram(cr)
        rpr.apply_gates_from_circuit(cr, cr)
        self.assertEqual(sample.state.bitstring, rpr.rbits.to01())

    def test_qcircuit_to_rprogram_with_qroutines(self):
        pr = Program()
        qr = pr.qalloc(5)
        for qb in qr:
            pr.apply(X, qb)
        qfun = _m_gate3(4)
        pr.apply(qfun, qr[1], qr[0], qr[4], qr[2])

        cr = pr.to_circ(include_matrices=False, submatrices_only=True)
        res = self.qpu.submit(cr.to_job())
        sample = None
        for sample in res:
            pass
        assert sample is not None
        rpr = RProgram.circuit_to_rprogram(cr)
        rpr.apply_gates_from_circuit(cr, cr)
        self.assertEqual(sample.state.bitstring, rpr.rbits.to01())

    def test_qcircuit_to_rprogram_with_build_gates(self):
        pr = Program()
        qr = pr.qalloc(6)
        for qb in qr:
            pr.apply(X, qb)
        qfun_param = _m_gate2(4)
        pr.apply(qfun_param, qr[1], qr[3], qr[4], qr[2])

        cr = pr.to_circ(include_matrices=False, submatrices_only=True)
        res = self.qpu.submit(cr.to_job())
        sample = None
        for sample in res:
            pass
        assert sample is not None
        rpr = RProgram.circuit_to_rprogram(cr)
        rpr.apply_gates_from_circuit(cr, cr)
        self.assertEqual(sample.state.bitstring, rpr.rbits.to01())

    def test_qroutine_to_rprogram_apply(self):
        pr = Program()
        qr = pr.qalloc(self.nrbits)
        for i, qb in enumerate(qr[:3]):
            pr.apply(X, qb)
            self.rcr.apply(RGate.NOT, i)
        qrout = _m_gate3(self.nrbits)
        pr.apply(qrout, qr)
        cr = pr.to_circ()
        self.rcr.apply_gates_from_qroutine(qrout)

        res = self.qpu.submit(cr.to_job())
        sample = None
        for sample in res:
            pass
        assert sample is not None

        self.assertEqual(sample.state.bitstring, self.rcr.rbits.to01())

    def test_qroutine_to_rprogram_apply_diff_map(self):
        pr = Program()
        qr = pr.qalloc(self.nrbits)
        for i, qb in enumerate(qr[:3]):
            pr.apply(X, qb)
            self.rcr.apply(RGate.NOT, i)
        tgt_qbits = qr[3:-2]
        qrout = _m_gate3(len(tgt_qbits))
        pr.apply(qrout, tgt_qbits)
        cr = pr.to_circ()
        self.rcr.apply_gates_from_qroutine(qrout, [qb.index for qb in tgt_qbits])

        res = self.qpu.submit(cr.to_job())
        sample = None
        for sample in res:
            pass
        assert sample is not None

        self.assertEqual(sample.state.bitstring, self.rcr.rbits.to01())
