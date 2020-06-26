import logging
from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qat.lang.AQASM import Program

from qat.external.utils.qroutines.hamming_weight_generate import benes_network


class BenesTestCase(CircuitTestCase):
    @classmethod
    def setUpClass(cls):
        CircuitTestCase.setUpClass()
        perm_logger = logging.getLogger(
            'isdquantum.qroutins.hamming_weight_generate')
        perm_logger.setLevel(cls.logger.level)
        perm_logger.handlers = cls.logger.handlers

    def setUp(self):
        self.circuit = Program()

    @parameterized.expand([
        ('n4w1', 4, 1, False),
        ('n4w1r', 4, 1, True),
        ('n4w2', 4, 2, False),
        ('n4w2r', 4, 2, True),
        ('n4w3', 4, 3, False),
        ('n4w3r', 4, 3, True),
        ('n8w1', 8, 1, False),
        ('n8w1r', 8, 1, True),
        ('n8w2', 8, 2, False),
        ('n8w2r', 8, 2, True),
        ('n8w3', 8, 3, False),
        ('n8w3r', 8, 3, True),
        ('n8w4', 8, 4, False),
        ('n8w4r', 8, 4, True),
        ('n8w5', 8, 5, False),
        ('n8w5r', 8, 5, True),
        ('n8w6', 8, 6, False),
        ('n8w6r', 8, 6, True),
        ('n8w7', 8, 7, False),
        ('n8w7r', 8, 7, True),
        # too much memory
        # ('n16w1', 16, 1, False),
        # ('n16w1r', 16, 1, True),
    ])
    def test_patterns(self, name, n, w, reverse):
        permutation_dict = benes_network.get_generate_pattern(n, w)
        self.logger.debug("n_flips = {0}".format(permutation_dict['n_flips']))
        self.logger.debug("n_lines = {0}".format(permutation_dict['n_lines']))
        selectors_q = self.circuit.qalloc(permutation_dict['n_lines'])
        flip_q = self.circuit.qalloc(permutation_dict['n_flips'])
        self.logger.debug(len(flip_q))

        qf = benes_network.generate(selectors_q, flip_q, permutation_dict)
        self.circuit.apply(qf, *selectors_q, *flip_q)

        res = self.qpu.submit(self.circuit.to_circ().to_job(
            qubits=[q.index for q in selectors_q]))

        for sample in res:
            bitstring = str(bin(sample.state.state))
            self.assertEqual(bitstring.count("1", 2), w)
