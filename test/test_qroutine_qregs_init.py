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
        qreg = prog.qalloc(bits)
        qfun = qregs.initialize_qureg_given_int(int_dec, bits, little_endian)
        prog.apply(qfun, qreg)
        # self.draw_program(prog, circ_kwargs={'do_link': False})
        res = self.qpu.submit(prog.to_circ().to_job())
        state = res.raw_data[0].state.state

        if not little_endian:
            self.assertEqual(state, int_dec)
        else:
            tmp = conversion.get_bitstring_from_int(state, bits)
            tmp = conversion.get_int_from_bitstring(tmp, littleEndian=True)
            self.assertEqual(tmp, int_dec)
