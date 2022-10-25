import functools
from test.common import BasicTestCase

from qat.external.qpus.reversible import ReversibleGate, ReversibleQPU


class TestReversibleQPU(BasicTestCase):
    nqbits = 10

    def setUp(self):
        super().setUp()
        self.rpu = ReversibleQPU()
        self.rpu.qalloc(self.nqbits)
        self._test_arr = ['0'] * self.nqbits

    def test_not(self):
        self.rpu.apply(ReversibleGate.NOT, None, 1)
        self._test_arr[1] = '1'
        self.assertEqual(self.rpu.qbits.to01(), ''.join(self._test_arr))

    def test_mnot(self):
        lst = {1, 3, 4, 9}
        self.rpu.apply(ReversibleGate.NOT, None, lst)
        for i in lst:
            self._test_arr[i] = '1'
        self.assertEqual(self.rpu.qbits.to01(), ''.join(self._test_arr))

    def test_swap(self):
        self.rpu.apply(ReversibleGate.NOT, None, 3)
        self.rpu.apply(ReversibleGate.SWAP, None, {3, 2})
        self._test_arr[2] = '1'
        self.assertEqual(self.rpu.qbits.to01(), ''.join(self._test_arr))

    def test_not_disjoints(self):
        # self.rpu.apply(ReversibleGate.NOT, None, 3)
        self.rpu.qbits.invert(3)
        self.rpu.qbits.invert(4)
        part = functools.partial(self.rpu.apply, ReversibleGate.NOT, {3, 4},
                                 {4, 5})
        self.assertRaises(ValueError, part)

    def test_mcmnot(self):
        trgts = {1, 3, 4, 9}
        ctrls = {2, 5}
        for i in ctrls:
            self.rpu.qbits.invert(i)
            self._test_arr[i] = '1'
        for i in trgts:
            self._test_arr[i] = '1'
        self.rpu.apply(ReversibleGate.NOT, ctrls, trgts)
        self.assertEqual(self.rpu.qbits.to01(), ''.join(self._test_arr))
