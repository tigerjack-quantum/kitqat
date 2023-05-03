from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qat.external.qroutines import qregs_init as qrinit
from qat.external.qroutines.qubitrotate import mine
from qat.lang.AQASM.program import Program


class TestRotations(CircuitTestCase):
    @parameterized.expand(["1011", "0101", "100110", "110010", "000100111"])
    def test_left_rotate(self, bitstring):
        pr = Program()
        qr = pr.qalloc(len(bitstring))
        qf_init = qrinit.initialize_qureg_given_bitstring(bitstring, True)
        pr.apply(qf_init, qr)
        qf_rot = mine.left_rotate(len(bitstring))
        pr.apply(qf_rot, qr)
        cr = pr.to_circ()
        res = self.simulate_circuit(cr)
        self.assertEqual(len(res), 1)
        exp = bitstring[1:] + bitstring[0]
        for sample in res:
            self.assertEqual(sample.state.bitstring, exp[::-1])
