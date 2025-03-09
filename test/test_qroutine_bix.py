import itertools
import unittest
from math import ceil, log2
from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qatext.qpus.reversible import RProgram
from qatext.qroutines import bix, qregs_init
from qatext.qroutines.arith import cuccaro_arith
from qat.lang.AQASM.program import Program

# from qat.lang.AQASM.aqasm_util import InvalidGateArguments


class BixTestCase(CircuitTestCase):
    def _test_bix_fixed_weight_common(self, bitstring):
        n = len(bitstring)
        # the additional + 1 is required since we want indexes starting from 1
        # to n (and not the traditional 0 to n-1)
        # add should be 0 for not idx_start_at_one
        for index_start_at_one in (True, False):
            with self.subTest(index_start_at_one=index_start_at_one):
                add = 1 if index_start_at_one else 0
                l2n = int(ceil(log2(n + add)))
                onesexp = [
                    bin(i + add)[2:].zfill(l2n)
                    for i, j in enumerate(bitstring)
                    if j == "1"
                ]
                zerosexp = [
                    bin(i + add)[2:].zfill(l2n)
                    for i, j in enumerate(bitstring)
                    if j == "0"
                ]
                weight = len(onesexp)
                reg_names = {}

                pr = Program()
                wreg = pr.qalloc(n)
                reg_names[f"wreg"] = range(wreg.start, wreg.length)
                oregs = []
                zregs = []
                for i in range(weight):
                    qr = pr.qalloc(l2n)
                    oregs.append(qr)
                    reg_names[f"oregs_{i}"] = range(qr.start, qr.start + qr.length)
                for i in range(n - weight):
                    qr = pr.qalloc(l2n)
                    zregs.append(qr)
                    reg_names[f"zregs_{i}"] = range(qr.start, qr.start + qr.length)

                pr.apply(
                    qregs_init.initialize_qureg_given_bitstring(
                        bitstring, little_endian=False
                    ),
                    wreg,
                )

                qfun = bix.bix_fixed_weight_v2(n, weight, index_start_at_one)
                pr.apply(qfun, wreg, *oregs, *zregs)

                circ = pr.to_circ(link=[cuccaro_arith.adder, cuccaro_arith.subtractor])
                # circ = pr.to_circ(link=[tkk_arith.adder])

                obtained = None
                if self.REVERSIBLE_ON:
                    rpr = RProgram.circuit_to_rprogram(circ, reg_names)
                    obtained = rpr.rbits.to01()
                else:
                    res = self.qpu.submit(circ.to_job())
                    counts = len(res)
                    self.assertEqual(counts, 1)
                    for sample in res:
                        if self.SIMULATOR == "linalg":
                            self.assertEqual(sample.probability, 1)
                        obtained = sample.state.bitstring
                ones = []
                zeros = []
                assert obtained is not None
                for k, v in reg_names.items():
                    if k.startswith("oregs_"):
                        ones.append(obtained[v.start : v.stop])
                    elif k.startswith("zregs_"):
                        zeros.append(obtained[v.start : v.stop])

                self.assertEqual(obtained[wreg.start : wreg.length], bitstring)
                for obt, exp in itertools.chain(
                    zip(ones, onesexp), zip(zeros, zerosexp)
                ):
                    self.assertEqual(obt, exp)

                ancillae_start = zregs[-1].start + zregs[-1].length
                for i in bitstring[ancillae_start:]:
                    self.assertEqual(i, "0")


    @parameterized.expand(
        [
            "0101",
            "0001",
            "1000",
            "1101",
            "10011",
            "11011",
            "0001101",
            "1111000",
            "10110100",
            "11001011",
            "111001011",
        ]
    )
    @unittest.skipUnless(
        CircuitTestCase.REVERSIBLE_ON, f"Only enabled with reversible simulation"
    )
    def test_bix_fixed_weight_large(self, bitstring):
        self._test_bix_fixed_weight_common(bitstring)
