import random
import unittest
from test.common_circuit import CircuitTestCase
from qat.external.qroutines import qregs_init as qregs

from parameterized import parameterized
from qat.external.qpus.reversible import RProgram
from qat.external.qroutines.qubitshuffle import reverse
from qat.external.qroutines.qubitshuffle import rotate
from qat.lang.AQASM.program import Program


class QubitShuffle(CircuitTestCase):
    @parameterized.expand(
        [
            "0111",
            "0001",
            "1000",
            "1101",
            "10011",
            "1111000",
            "10110100",
            "11001011",
            "111001011",
        ]
    )
    def test_reverse(self, bitstring):
        n = len(bitstring)
        pr = Program()
        qr = pr.qalloc(n)

        qfun = qregs.initialize_qureg_given_bitstring(bitstring, False)
        pr.apply(qfun, qr)

        qfun = reverse.reverse(n)
        pr.apply(qfun, qr)

        circ = pr.to_circ()
        exp = bitstring[::-1]
        if self.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(circ)
            obtained = rpr.rbits.to01()
        else:
            res = self.qpu.submit(circ.to_job())
            # self.logger.debug("res %s", res)
            counts = len(res)
            self.assertEqual(counts, 1)
            for sample in res:
                if self.SIMULATOR == "linalg":
                    self.assertEqual(sample.probability, 1)
            obtained = sample.state.bitstring
        self.assertEqual(obtained, exp)

    @parameterized.expand(
        [
            ("0111", 1),
            ("0001", 2),
            ("1000", 3),
            ("1101", 4),
            ("10011", 3),
            ("1111000", 2),
            ("10110100", 1),
            ("11001011", 5),
            ("111001011", 6),
        ]
    )
    def test_rotate(self, bitstring, d):
        n = len(bitstring)
        pr = Program()
        qr = pr.qalloc(n)

        qfun = qregs.initialize_qureg_given_bitstring(bitstring, False)
        pr.apply(qfun, qr)
        qfun = rotate.reversal(n, d)
        pr.apply(qfun, qr)
        circ = pr.to_circ()

        d1 = d%n
        exp = bitstring[d1:] + bitstring[:d1]
        if self.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(circ)
            obtained = rpr.rbits.to01()
        else:
            res = self.qpu.submit(circ.to_job())
            # self.logger.debug("res %s", res)
            counts = len(res)
            self.assertEqual(counts, 1)
            for sample in res:
                if self.SIMULATOR == "linalg":
                    self.assertEqual(sample.probability, 1)
            obtained = sample.state.bitstring
        self.assertEqual(obtained, exp)
