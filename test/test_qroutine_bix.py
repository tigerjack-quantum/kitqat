from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qat.external.qpus.reversible import RProgram
from qat.external.qroutines import qregs_init
from qat.external.qroutines.qubitshuffle import reverse, rotate
from qat.external.qroutines import bix
from qat.lang.AQASM.program import Program
from qat.external.qroutines.arith import tkk_arith, cuccaro_arith
from qat.external.utils.qatmgmt import results

from math import ceil, log2

# from qat.lang.AQASM.aqasm_util import InvalidGateArguments


class BixTestCase(CircuitTestCase):
    @parameterized.expand(
        [
            "0101",
            # "0001",
            # "1000",
            # "1101",
            # "10011",
            # "1111000",
            # "10110100",
            # "11001011",
            # "111001011",
        ]
    )
    def test_bix_fixed_weight(self, bitstring):
        n = len(bitstring)
        # the additional + 1 is required since we want indexes starting from 1
        # to n (and not the traditional 0 to n-1)
        # add should be 0 for not idx_start_at_one
        add = 1
        l2n = int(ceil(log2(n + add)))
        ones = [
            bin(i + add)[2:].zfill(l2n) for i, j in enumerate(bitstring) if j == "1"
        ]
        zeros = [
            bin(i + add)[2:].zfill(l2n) for i, j in enumerate(bitstring) if j == "0"
        ]
        weight = len(ones)
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
            qregs_init.initialize_qureg_given_bitstring(bitstring, little_endian=False),
            wreg,
        )

        qfun = bix.bix_fixed_weight(n, weight, True)
        pr.apply(qfun, wreg, *oregs, *zregs)

        circ = pr.to_circ(link=[cuccaro_arith.adder])
        # circ = pr.to_circ(link=[tkk_arith.adder])

        obtained = None
        if self.REVERSIBLE_ON:
            print(reg_names)
            rpr = RProgram.circuit_to_rprogram(circ, reg_names)
            obtained = rpr.rbits.to01()
            print(rpr.get_result_by_name())
        else:
            res = self.qpu.submit(circ.to_job())
            counts = len(res)
            self.assertEqual(counts, 1)
            for sample in res:
                if self.SIMULATOR == "linalg":
                    self.assertEqual(sample.probability, 1)
                obtained = sample.state.bitstring
        print(ones)
        print(zeros)
        print(obtained)
        self.draw_circuit(circ, max_depth=2)
        # self.assertEqual(obtained, exp)
