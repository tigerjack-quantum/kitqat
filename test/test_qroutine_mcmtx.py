from copy import deepcopy

from parameterized import parameterized
from qat.external.utils.qroutines import fake
from qat.external.utils.qroutines.mctrls import mcx
from qat.lang.AQASM import CCNOT, H, Program, X

from .common_circuit import CircuitTestCase


class MctrlsTest(CircuitTestCase):
    def test_mccnot(self):
        pr = Program()
        qr = pr.qalloc(5)

        for qb in qr:
            pr.apply(H, qb)

        pr2 = deepcopy(pr)
        pr.apply(CCNOT, qr[:3])
        pr.apply(CCNOT, qr[0], qr[1], qr[3])
        pr.apply(CCNOT, qr[0], qr[1], qr[4])
        res = self.qpu.submit(pr.to_circ().to_job())

        for global_phase in (True, False):
            with self.subTest(global_phase=global_phase):
                pr2 = deepcopy(pr2)
                pr2.apply(mcx.mccnot(3, global_phase), pr2.registers[0])

                res2 = self.qpu.submit(pr2.to_circ().to_job())

                for sample, sample2 in zip(res, res2):
                    self.assertEqual(sample.state.state, sample2.state.state)
                    if not global_phase:
                        self.assertEqual(sample.probability,
                                         sample2.probability)
                    else:
                        self.assertEqual(sample.amplitude, sample2.amplitude)

    def test_mcccnot(self):
        pr = Program()
        qr = pr.qalloc(5)

        for qb in qr:
            pr.apply(H, qb)

        pr2 = deepcopy(pr)
        pr.apply(CCNOT.ctrl(), qr[:4])
        pr.apply(CCNOT.ctrl(), qr[:3], qr[4])
        res = self.qpu.submit(pr.to_circ().to_job())

        for global_phase in (True, False):
            with self.subTest(global_phase=global_phase):
                pr2 = deepcopy(pr2)
                pr2.apply(mcx.mcccnot(2, global_phase), pr2.registers[0])
                res2 = self.qpu.submit(pr2.to_circ().to_job())

                for sample, sample2 in zip(res, res2):
                    self.assertEqual(sample.state.state, sample2.state.state)
                    if not global_phase:
                        self.assertEqual(sample.probability,
                                         sample2.probability)
                    else:
                        # Note how, with global phase (and hence manually
                        # derived abstract gates) we loose precision
                        self.assertAlmostEqual(sample.amplitude,
                                               sample2.amplitude)

    def _common_mcmtx_1tft(self):
        pr = Program()
        qr = pr.qalloc(5)
        fake.add_fake_following_pattern(pr, {'ctrl': qr[:-1], 'tgt': [qr[-1]]})

        for qb in qr[:-1]:
            pr.apply(X, qb)

        pr.apply(mcx.MCMTX(len(qr) - 1, 1, 2), qr[:-1], qr[-1])
        return pr

    @parameterized.expand([
        (mcx.mcmtx_vshape, ),
        # (mct.mcmtx_barenco1, )
    ])
    def test_1tgt(self, mode):
        pr = self._common_mcmtx_1tft()
        res = self.qpu.submit(pr.to_circ(link=[mode]).to_job())
        self.assertEqual(len(res.raw_data), 1)
        self.assertEqual(res.raw_data[0].state.bitstring, '1111100')
        self.assertEqual(res.raw_data[0].probability, 1)
