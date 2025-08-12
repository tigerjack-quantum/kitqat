from copy import deepcopy

from parameterized import parameterized
from qat.lang.AQASM.gates import CCNOT, H, X
from qat.lang.AQASM.program import Program
from qatext.synthesis.mctrls import mcx
from qatext.qatmgmt.program import ProgramWrapper

from test.common_circuit import CircuitTestCase


class MctrlsTest(CircuitTestCase):

    @parameterized.expand([
        ("sqrt", mcx.mccnot_sqrroot),
        ("ht", mcx.mccnot_ht),
    ])
    def test_mccnot(self, name, implementation):
        pr = Program()
        nqbits = 5
        qr = pr.qalloc(nqbits)

        for qb in qr:
            pr.apply(H, qb)

        pr2 = deepcopy(pr)
        for qb in qr[2:]:
            pr.apply(CCNOT, qr[0], qr[1], qb)
        res = self.qpu.submit(pr.to_circ().to_job())

        global_phases = (True, False) if name == "sqrt" else (False, )

        for global_phase in global_phases:
            with self.subTest(global_phase=global_phase):
                pr2 = deepcopy(pr2)
                pr2.apply(mcx.MTCCNOT(nqbits - 2, global_phase),
                          pr2.registers[0])

                res2 = self.qpu.submit(
                    pr2.to_circ(link=[implementation]).to_job())

                for sample, sample2 in zip(res, res2):
                    self.assertEqual(sample.state.state, sample2.state.state)
                    if not global_phase:
                        self.assertAlmostEqual(sample.probability,
                                               sample2.probability)
                    else:
                        self.assertAlmostEqual(sample.amplitude,
                                               sample2.amplitude)

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
        prw = ProgramWrapper(Program())
        qr = prw.qalloc(5)
        prw.add_name_to_qbits_following_pattern({
            "ctrl": qr[:-1],
            "tgt": [qr[-1]]
        })

        for qb in qr[:-1]:
            prw.apply(X, qb)

        prw.apply(mcx.MCMTX(len(qr) - 1, 1, 2), qr[:-1], qr[-1])
        return prw

    @parameterized.expand([
        (mcx.mcmtx_vshape, ),
        # (mct.mcmtx_barenco1, )
    ])
    def test_1tgt(self, mode):
        pr = self._common_mcmtx_1tft()
        res = self.qpu.submit(pr.to_circ(link=[mode]).to_job())
        self.assertEqual(len(res), 1)
        for sample in res:
            if sample.state.bitstring == "1111100":
                self.assertEqual(sample.probability, 1)
