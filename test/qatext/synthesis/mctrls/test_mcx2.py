import unittest
from test.common_circuit import CircuitTestCase

from qat.lang.AQASM.gates import X
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import RProgram
from qatext.synthesis.mctrls import mcx2


class MctrlsXTest(CircuitTestCase):

    def _get_program(self, bitstring):
        pr = Program()
        ctrls = pr.qalloc(len(bitstring))
        tgt = pr.qalloc(1)
        for ctrl, bit in zip(ctrls, bitstring):
            if bit == '1':
                pr.apply(X, ctrl)
        pr.apply(X.ctrl(len(bitstring)), ctrls, tgt)
        return pr

    def _mcx_test(self, nctrls):
        for i in reversed(range(2**nctrls)):
            bitstring = bin(i)[2:].zfill(nctrls)
            with self.subTest(bitstring=bitstring):
                pr = self._get_program(bitstring)
                cr = pr.to_circ(link=[mcx2.x], include_matrices=False, inline=True, include_locks=True)
                cr = pr.to_circ(link=[mcx2.mnot], include_matrices=False, inline=True, include_locks=True)
                # cr.display()
                rpr = RProgram.circuit_to_rprogram(cr)
                rpr.apply_gates_from_circuit(cr, cr)
                obtained = rpr.rbits.to01()
                if bitstring == '1'*nctrls:
                    self.assertEqual(obtained[nctrls], '1')
                else:
                    self.assertEqual(obtained[nctrls], '0')
    def test_mcx(self):
        nexp = 2
        nctrls = 2**nexp
        self._mcx_test(nctrls)

    @unittest.skipUnless(
        CircuitTestCase.SLOW_TEST_ON,
        CircuitTestCase.SLOW_TEST_ON_REASON,
    )
    def test_mcx_slow(self):
        nexp = 4
        nctrls = 2**nexp
        self._mcx_test(nctrls)
                
