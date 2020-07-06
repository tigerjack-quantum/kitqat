from parameterized import parameterized
from qat.external.utils.synthesis.roots.paulis import nrootx, nrooty, nrootz
from qat.lang.AQASM import Program, X

from test.common_circuit import CircuitTestCase


class NrootxTest(CircuitTestCase):
    @parameterized.expand([(1, ), (2, ), (3, ), (4, ), (5, )])
    def test_xequivalence(self, n):
        for global_phase in (True, False):
            with self.subTest(global_phase=global_phase):
                pr = Program()
                qr = pr.qalloc(1)
                gate = nrootx(n, global_phase)
                for i in range(n):
                    pr.apply(gate, qr)
                res = self.qpu.submit(pr.to_circ().to_job())
                self.assertEqual(len(res.raw_data), 1)
                self.assertEqual(res.raw_data[0].state.int, 1)
                if not global_phase:
                    self.assertAlmostEqual(res.raw_data[0].probability, 1)
                else:
                    self.assertAlmostEqual(res.raw_data[0].amplitude, 1)

    @parameterized.expand([(1, ), (2, ), (3, ), (4, ), (5, )])
    def test_yequivalence(self, n):
        for global_phase in (True, False):
            with self.subTest(global_phase=global_phase):
                pr = Program()
                qr = pr.qalloc(1)
                pr.apply(X, qr[0])
                gate = nrooty(n, global_phase)
                for i in range(n):
                    pr.apply(gate, qr)
                res = self.qpu.submit(pr.to_circ().to_job())
                self.assertEqual(len(res.raw_data), 1)
                self.assertEqual(res.raw_data[0].state.int, 0)
                if not global_phase:
                    self.assertAlmostEqual(res.raw_data[0].probability, 1)
                else:
                    self.assertAlmostEqual(res.raw_data[0].amplitude, -1j)

    @parameterized.expand([(1, ), (2, ), (3, ), (4, ), (5, )])
    def test_zequivalence(self, n):
        for global_phase in (True, False):
            with self.subTest(global_phase=global_phase):
                pr = Program()
                qr = pr.qalloc(1)
                pr.apply(X, qr[0])
                gate = nrootz(n, global_phase)
                for i in range(n):
                    pr.apply(gate, qr)
                res = self.qpu.submit(pr.to_circ().to_job())
                self.assertEqual(len(res.raw_data), 1)
                self.assertEqual(res.raw_data[0].state.int, 1)
                if not global_phase:
                    self.assertAlmostEqual(res.raw_data[0].probability, 1)
                else:
                    self.assertAlmostEqual(res.raw_data[0].amplitude, -1)
