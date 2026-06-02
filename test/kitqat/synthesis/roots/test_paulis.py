from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from kitqat.synthesis.roots.paulis import nrootx, nrooty, nrootz
from qat.lang.AQASM.gates import X
from qat.lang.AQASM.program import Program


class NrootxTest(CircuitTestCase):
    @parameterized.expand([(1,), (2,), (3,), (4,), (5,)])
    def test_xequivalence(self, n):
        for global_phase in (True, False):
            with self.subTest(global_phase=global_phase):
                pr = Program()
                qr = pr.qalloc(1)
                gate = nrootx(n, global_phase)
                for _ in range(n):
                    pr.apply(gate, qr)
                res = self.qpu.submit(pr.to_circ().to_job())
                self.assertEqual(len(res), 1)
                for sample in res:
                    if sample.state.int == 1:
                        self.assertAlmostEqual(sample.probability, 1)
                    if not global_phase:
                        self.assertAlmostEqual(sample.probability, 1)
                    else:
                        self.assertAlmostEqual(sample.amplitude, 1)
                    break

    @parameterized.expand([(1,), (2,), (3,), (4,), (5,)])
    def test_yequivalence(self, n):
        for global_phase in (True, False):
            with self.subTest(global_phase=global_phase):
                pr = Program()
                qr = pr.qalloc(1)
                pr.apply(X, qr[0])
                gate = nrooty(n, global_phase)
                for _ in range(n):
                    pr.apply(gate, qr)
                res = self.qpu.submit(pr.to_circ().to_job())

                for sample in res:
                    if sample.state.int == 0:
                        self.assertAlmostEqual(sample.probability, 1)
                    if not global_phase:
                        self.assertAlmostEqual(sample.probability, 1)
                    else:
                        self.assertAlmostEqual(sample.amplitude.real, 0)
                        self.assertAlmostEqual(sample.amplitude.imag, -1)
                    break

    @parameterized.expand([(1,), (2,), (3,), (4,), (5,)])
    def test_zequivalence(self, n):
        for global_phase in (True, False):
            with self.subTest(global_phase=global_phase):
                pr = Program()
                qr = pr.qalloc(1)
                pr.apply(X, qr[0])
                gate = nrootz(n, global_phase)
                for _ in range(n):
                    pr.apply(gate, qr)
                res = self.qpu.submit(pr.to_circ().to_job())

                for sample in res:
                    if sample.state.int == 1:
                        self.assertAlmostEqual(sample.probability, 1)
                    if not global_phase:
                        self.assertAlmostEqual(sample.probability, 1)
                    else:
                        self.assertAlmostEqual(sample.amplitude, -1)
                    break
