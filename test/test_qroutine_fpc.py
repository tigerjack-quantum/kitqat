import unittest
from math import factorial
from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qat.lang.AQASM import H, Program

from qat.external.utils.qroutines import qregs_init as qregs
from qat.external.utils.qroutines.hamming_weight_compute import fpc

DEBUG = False


class PopulationCountTestCase(CircuitTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.logger.level != 0:
            fpc.LOGGER.setLevel(cls.logger.level)
            for handler in cls.logger.handlers:
                fpc.LOGGER.addHandler(handler)

    @parameterized.expand([
        ("0000"),
        ("0101"),
        ("0001"),
        ("1101"),
        ("1001"),
        ("1111"),
        ("10110100"),
        ("11001011"),
        ("11010000"),
    ])
    @unittest.skipIf(DEBUG, "already working")
    def test_fpc_weight_compute(self, name):
        nwr_dict = fpc.get_qroutine_for_qubits_weight_get_pattern(len(name))
        self.logger.debug("nwr_dict %s", nwr_dict)
        program = Program()

        a = program.qalloc(nwr_dict['n_lines'])
        cout = program.qalloc(nwr_dict['n_couts'])
        self.logger.debug("a %s", a)
        self.logger.debug("cout %s", cout)

        qfun = qregs.initialize_qureg_given_bitstring(name, True)
        program.apply(qfun, a)

        qfun = fpc.get_qroutine_for_qubits_weight(len(a), len(cout), nwr_dict)
        program.apply(qfun, a, cout)

        to_measure_qubits = fpc.get_to_measure_qubits(a, cout, nwr_dict)

        res = self.qpu.submit(program.to_circ().to_job(
            qubits=[qb.index for qb in to_measure_qubits]))
        self.logger.debug("res %s", res)

        counts = len(res)
        self.assertEqual(counts, 1)
        exp_w = name.count("1")
        if self.SIMULATOR == 'linalg':
            # For QLM
            for sample in res:
                if sample.state.lsb_int == exp_w:
                    self.assertEqual(sample.probability, 1)
                    break
        elif self.SIMULATOR == 'pylinalg':
            # in myQLM, we get only one state
            state = res[0].state
            self.assertEqual(state.lsb_int, exp_w)

    @parameterized.expand([
        ("0on2", 0, 2),
        ("1on2", 1, 2),
        ("2on2", 2, 2),
        ("0on4", 0, 4),
        ("2on4", 2, 4),
        ("3on4", 3, 4),
        ("3on8", 1, 8),
        ("3on8", 2, 8),
        ("3on8", 3, 8),
        ("3on8", 4, 8),
    ])
    @unittest.skipIf(DEBUG, "already working")
    def test_fpc_hadamards_weight_check(self, name, weight_int, n_bits):
        nwr_dict = fpc.get_qroutine_for_qubits_weight_get_pattern(n_bits)

        program = Program()
        a = program.qalloc(nwr_dict['n_lines'])
        cout = program.qalloc(nwr_dict['n_couts'])
        eq = program.qalloc(1)
        self.logger.debug("a %s", a)
        self.logger.debug("cout %s", cout)
        for qb in a:
            program.apply(H, qb)
        qfun = fpc.get_qroutine_for_qubits_weight_check(
            len(a), len(cout), weight_int, nwr_dict, True)
        program.apply(qfun, a, cout, eq)
        qfun = fpc.get_qroutine_for_qubits_weight_check(len(a),
                                                        len(cout),
                                                        weight_int,
                                                        nwr_dict,
                                                        False)
        program.apply(qfun.dag(), a, cout)
        res = self.qpu.submit(program.to_circ().to_job(qubits=[a, eq]))
        self.logger.debug("res %s", res)

        counts = len(res)
        self.assertEqual(counts, 2**len(a))
        total_actives = 0
        for sample in res:
            state = sample.state
            bitstring = state.bitstring
            if bitstring[-1] == '1':
                total_actives += 1
                # + 1 bcz we have the eq qbits, should be faster than slicing
                self.assertEqual(bitstring.count("1"), weight_int + 1)
            else:
                self.assertNotEqual(bitstring.count("1"), weight_int)
        exp_actives = factorial(n_bits) / factorial(weight_int) / factorial(
            n_bits - weight_int)
        self.assertEqual(total_actives, exp_actives)
