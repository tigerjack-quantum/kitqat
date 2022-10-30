import functools
from test.common import BasicTestCase

from qat.external.qpus.reversible import RGate, RProgram
from qat.lang.AQASM.gates import CCNOT, CNOT, SWAP, H, X
from qat.lang.AQASM.program import Program
from qat.pylinalg import PyLinalg


class TestRProgram(BasicTestCase):
    nrbits = 10

    def setUp(self):
        super().setUp()
        self.rcr = RProgram()
        self.rcr.qalloc(self.nrbits)
        self._test_arr = ['0'] * self.nrbits

    def test_not(self):
        self.rcr.apply(RGate.NOT, None, 1)
        self._test_arr[1] = '1'
        self.assertEqual(self.rcr.rbits.to01(), ''.join(self._test_arr))

    def test_mnot(self):
        lst = {1, 3, 4, 9}
        self.rcr.apply(RGate.NOT, None, lst)
        for i in lst:
            self._test_arr[i] = '1'
        self.assertEqual(self.rcr.rbits.to01(), ''.join(self._test_arr))

    def test_swap(self):
        self.rcr.apply(RGate.NOT, None, 3)
        self.rcr.apply(RGate.SWAP, None, {3, 2})
        self._test_arr[2] = '1'
        self.assertEqual(self.rcr.rbits.to01(), ''.join(self._test_arr))

    def test_not_disjoints(self):
        self.rcr.rbits.invert(3)
        self.rcr.rbits.invert(4)
        part = functools.partial(self.rcr.apply, RGate.NOT, {3, 4}, {4, 5})
        self.assertRaises(ValueError, part)

    def test_mcmnot(self):
        trgts = {1, 3, 4, 9}
        ctrls = {2, 5}
        for i in ctrls:
            self.rcr.rbits.invert(i)
            self._test_arr[i] = '1'
        for i in trgts:
            self._test_arr[i] = '1'
        self.rcr.apply(RGate.NOT, ctrls, trgts)
        self.assertEqual(self.rcr.rbits.to01(), ''.join(self._test_arr))

    def test_program_to_rprogram_error(self):
        pr = Program()
        pr.apply(H, pr.qalloc(1))

        part = functools.partial(RProgram.circuit_to_rprogram, pr.to_circ())
        self.assertRaises(AttributeError, part)

    def test_rcircuit_to_rprogram(self):
        pr = Program()
        qr = pr.qalloc(5)
        pr.apply(X, qr[0])
        pr.apply(X, qr[4])
        pr.apply(SWAP, qr[4], qr[3])
        pr.apply(CNOT, qr[:2])
        pr.apply(CCNOT, qr[:3])
        pr.apply(SWAP, qr[2], qr[4])
        # Note that this last 2 gates are not applied since their ctrls are not all 1's
        pr.apply(CCNOT, qr[2:5])
        pr.apply(SWAP.ctrl(3), qr)
        qpu = PyLinalg()
        cr = pr.to_circ()
        res = qpu.submit(cr.to_job())
        sample = None
        for sample in res:
            pass
        assert sample is not None
        rpr = RProgram.circuit_to_rprogram(cr)
        print()
        self.assertEqual(sample.state.bitstring, rpr.rbits.to01())
