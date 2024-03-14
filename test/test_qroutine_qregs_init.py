from qatext.qpus.reversible import RProgram
from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qatext.utils.bits import conversion, misc
from qatext.qroutines import qregs_init as qregs
from qat.lang.AQASM.program import Program


class QregInitTestCase(CircuitTestCase):
    @parameterized.expand(
        [
            (0, False),
            (0, True),
            (7, False),
            (7, True),
            (8, False),
            (8, True),
            (15, False),
            (15, True),
        ]
    )
    def test_adder(self, int_dec, little_endian):
        prog = Program()
        bits = misc.get_required_bits(int_dec)

        # in big endian qreg[0] has the MSB, while in little endian qreg[n-1]
        # has the MSB. However, the result from circuit simulation will always
        # be from bottom to top (considering circuit drawing), which means it
        # is in little endian. For this reason, we create a new variable,
        # int_dec_new, containing the value we expect to see in the results.
        # F.e., if we have int_dec=8, little_endian=True, we have that the
        # bitstring will be 1000 and int_dec_new will be 1.
        tmp = conversion.get_bitstring_from_int(int_dec, bits)
        if little_endian:
            int_dec_new = conversion.get_int_from_bitstring(tmp, littleEndian=True)
        else:
            int_dec_new = int_dec
        qreg = prog.qalloc(bits)
        qfun = qregs.initialize_qureg_given_int(int_dec, bits, little_endian)
        prog.apply(qfun, qreg)

        circ = prog.to_circ()
        if self.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(circ)
            res = rpr.rbits.to01()
            if little_endian:
                res = res[::-1]
            self.assertEqual(res, tmp)

        else:
            res = self.qpu.submit(prog.to_circ().to_job())
            if self.SIMULATOR == "linalg":
                # For QLM
                for sample in res:
                    if sample.state.lsb_int == int_dec_new:
                        self.assertEqual(sample.probability, 1)
                        break
            elif self.SIMULATOR == "pylinalg":
                # myQLM
                state = res[0].state.state
                self.assertEqual(state, int_dec_new)
