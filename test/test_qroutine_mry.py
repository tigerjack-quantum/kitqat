import unittest
from copy import deepcopy
from math import pi
from random import random

from qat.external.utils.synthesis.mctrls import mry
from qat.lang.AQASM.gates import RY, H
from qat.lang.AQASM.program import Program

from .common_circuit import CircuitTestCase

# from qat.core.console import display


class MCRyTest(CircuitTestCase):
    def test_mcry(self):
        pr = Program()
        nqbits = 5
        qr = pr.qalloc(nqbits)

        for qb in qr:
            pr.apply(H, qb)

        pr2 = deepcopy(pr)
        qr2 = pr2.registers[0]
        for i in range(nqbits - 1):
            angle = random() * 2 * pi
            pr.apply(RY(angle).ctrl(), qr[i], qr[i + 1])
            pr2.apply(mry.MCRY(angle), qr2[i], qr2[i + 1])
        circ = pr.to_circ()
        circ2 = pr2.to_circ(link=[mry.mcry_simple])
        # print(statistics(circ))
        # print(statistics(circ2))
        # display(circ)
        # display(circ2, max_depth=1)
        res = self.qpu.submit(circ.to_job())
        res2 = self.qpu.submit(circ2.to_job())
        self.assertEqual(len(res2), len(res))
        for sample, sample2 in zip(
            sorted(res, key=lambda x: x.state.state),
            sorted(res2, key=lambda x: x.state.state),
        ):
            self.assertEqual(sample2.state.state, sample.state.state)
            self.assertAlmostEqual(sample2.amplitude, sample.amplitude)

    def test_mccry(self):
        pr = Program()
        nqbits = 5
        qr = pr.qalloc(nqbits)

        for qb in qr:
            pr.apply(H, qb)

        pr2 = deepcopy(pr)
        qr2 = pr2.registers[0]
        angles = []
        for i in range(nqbits - 2):
            angle = random() * 2 * pi
            angles.append(angle)
            pr.apply(RY(angle).ctrl(2), qr[i], qr[i + 1], qr[i + 2])
            pr2.apply(mry.MCCRY(angles[i]), qr2[i], qr2[i + 1], qr2[i + 2])
        circ = pr.to_circ()
        circ2 = pr2.to_circ(link=[mry.mccry_simple])
        # print(statistics(circ))
        # print(statistics(circ2))
        res = self.qpu.submit(circ.to_job())
        res2 = self.qpu.submit(circ2.to_job())
        self.assertEqual(len(res2), len(res))
        for sample, sample2 in zip(
            sorted(res, key=lambda x: x.state.state),
            sorted(res2, key=lambda x: x.state.state),
        ):
            self.assertEqual(sample2.state.state, sample.state.state)
            self.assertAlmostEqual(sample2.amplitude, sample.amplitude)

    @unittest.skip("WIP")
    def test_mcry2(self):
        pr = Program()
        nqbits = 5
        qr = pr.qalloc(nqbits)

        for qb in qr:
            pr.apply(H, qb)

        for i in range(nqbits - 1):
            angle = random() * 2 * pi
            pr.apply(RY(angle).ctrl(), qr[i], qr[i + 1])
        circ = pr.to_circ()
        circ2 = pr.to_circ(link=[mry.mcry_simple])
        # display(circ)
        # display(circ2, max_depth=2)
        # print(statistics(circ))
        # print(statistics(circ2))
        res = self.qpu.submit(circ.to_job())
        res2 = self.qpu.submit(circ2.to_job())
        self.assertEqual(len(res2), len(res))
        for sample, sample2 in zip(
            sorted(res, key=lambda x: x.state.state),
            sorted(res2, key=lambda x: x.state.state),
        ):
            self.assertEqual(sample2.state.state, sample.state.state)
            self.assertAlmostEqual(sample2.amplitude, sample.amplitude)
