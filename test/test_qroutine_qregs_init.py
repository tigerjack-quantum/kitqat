from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qat.external.utils.bits import conversion, misc
from qat.external.utils.qroutines import qregs_init as qregs
from qat.lang.AQASM.program import Program


class QregInitTestCase(CircuitTestCase):
    @parameterized.expand([
        (0, False),
        (0, True),
        (7, False),
        (7, True),
        (8, False),
        (8, True),
        (15, False),
        (15, True),
    ])
    def test_adder(self, int_dec, little_endian):
        prog = Program()
        bits = misc.get_required_bits(int_dec)
        if little_endian:
            tmp = conversion.get_bitstring_from_int(int_dec, bits)
            int_dec_new = conversion.get_int_from_bitstring(tmp, littleEndian=True)
        else:
            int_dec_new = int_dec
        qreg = prog.qalloc(bits)
        qfun = qregs.initialize_qureg_given_int(int_dec, bits, little_endian)
        prog.apply(qfun, qreg)
        res = self.qpu.submit(prog.to_circ().to_job())

        if self.SIMULATOR == 'linalg':
            # For QLM
            for sample in res:
                if sample.state.lsb_int == int_dec_new:
                    self.assertEqual(sample.probability, 1)
                    break
        elif self.SIMULATOR == 'pylinalg':
            # myQLM
            state = res[0].state.state
            self.assertEqual(state, int_dec_new)
