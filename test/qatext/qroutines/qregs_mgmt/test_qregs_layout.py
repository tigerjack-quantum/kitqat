from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import RProgram
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.qroutines.qregs_mgmt import qregs_layout as ql

# from qat.lang.AQASM.aqasm_util import InvalidGateArguments


class TestQregsLayout(CircuitTestCase):

    @parameterized.expand([
        "0111",
        "0001",
        "1000",
        "1101",
        "10011",
        "1111000",
        "10110100",
        "11001011",
        "111001011",
    ])
    def test_reverse(self, bitstring):
        n = len(bitstring)
        pr = Program()
        qr = pr.qalloc(n)

        qfun = qi.initialize_qureg_given_bitstring(bitstring, False)
        pr.apply(qfun, qr)

        qfun = ql.reverse(n)
        pr.apply(qfun, qr)

        circ = pr.to_circ()
        exp = bitstring[::-1]

        obtained = None
        if self.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(circ)
            rpr.apply_gates_from_circuit(circ, circ)
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

    @parameterized.expand([
        ("0111", 1),
        ("0001", 2),
        ("1000", 3),
        ("1101", 4),
        ("10011", 3),
        ("1111000", 2),
        ("10110100", 1),
        ("11001011", 5),
        ("111001011", 6),
    ])
    def test_rotate_qubits(self, bitstring, dshift):
        n = len(bitstring)
        for d in (-dshift, dshift):
            with self.subTest(bitstring=bitstring, d=d):
                pr = Program()
                qr = pr.qalloc(n)

                qfun = qi.initialize_qureg_given_bitstring(
                    bitstring, False)
                pr.apply(qfun, qr)

                qfun = ql.rotate(n, d)
                pr.apply(qfun, qr)
                circ = pr.to_circ()

                d1 = abs(d) % n
                if d > 0:
                    # left rotate
                    exp = bitstring[d1:] + bitstring[:d1]
                else:
                    # right rotate
                    exp = bitstring[n - d1:] + bitstring[:n - d1]

                obtained = None
                if self.REVERSIBLE_ON:
                    rpr = RProgram.circuit_to_rprogram(circ)
                    rpr.apply_gates_from_circuit(circ, circ)
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

    @parameterized.expand([
        (["0111", "0001", "0110"], 1),
        (["0111", "0001", "0110"], 2),
        (["0111", "0001", "0110"], 3),
        (["0111", "0001", "0110"], 4),
        # (["011", "0001", "0110"], 4), # different sizes, should fail
        (["10011", "11100", "11000", "10010", "10011"], 3),
        # (["10011", "11100", "11000", "10010", "10011"], 8),
    ])
    def test_rotate_qregs(self, bitstrings: list[str], dshift: int):
        nstrings = len(bitstrings)
        # for the rotate routine to work, every string should be of the same size
        lstrings = len(bitstrings[0])

        for d in (-dshift, dshift):
            with self.subTest(bitstrings=bitstrings, d=d):
                pr = Program()
                qregs = []
                for bitstring in bitstrings:
                    qr = pr.qalloc(lstrings)
                    qfun = qi.initialize_qureg_given_bitstring(
                        bitstring, False)
                    pr.apply(qfun, qr)
                    qregs.append(qr)

                qfun = ql.reg_rotate(nstrings, lstrings, d)
                pr.apply(qfun, *qregs)
                circ = pr.to_circ()

                d1 = abs(d) % nstrings
                if d > 0:
                    # left rotate
                    exp = bitstrings[d1:] + bitstrings[:d1]
                else:
                    # right rotate
                    exp = bitstrings[nstrings - d1:] + bitstrings[:nstrings -
                                                                  d1]
                # Since the result is a unique, long string
                exp = "".join([str(i) for i in exp])

                obtained = None
                if self.REVERSIBLE_ON:
                    rpr = RProgram.circuit_to_rprogram(circ)
                    rpr.apply_gates_from_circuit(circ, circ)
                    obtained = rpr.rbits.to01()
                else:
                    res = self.qpu.submit(circ.to_job())
                    counts = len(res)
                    self.assertEqual(counts, 1)
                    for sample in res:
                        if self.SIMULATOR == "linalg":
                            self.assertEqual(sample.probability, 1)
                        obtained = sample.state.bitstring
                self.assertEqual(obtained, exp)
