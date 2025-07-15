import logging
import unittest
from itertools import chain
from test import test_qroutine_bix
from test.common_circuit import CircuitTestCase, QRegsProperties

import numpy as np
from parameterized import parameterized
from qat.lang.AQASM.program import Program
from qatext.qroutines import bix, qregs_init
from qatext.qroutines.arith import cuccaro_arith

LOGGER = logging.getLogger(__name__)


class BixTestCase(CircuitTestCase):

    def extract_and_check_named_regs(self, bitstring, reg_name_to_slice,
                                     expected_map):
        """Post-processing checks"""
        for name, expected in expected_map.items():
            bits = bitstring[reg_name_to_slice[name]]
            self.assertEqual(bits, expected)

    def _run_test_bix(self,
                      n,
                      m,
                      weight,
                      bitstring,
                      exp_ones,
                      exp_zeros,
                      bix_func,
                      runtime_data=False):
        qregs_properties: dict[str, QRegsProperties] = {}

        reg_name_to_size = {}
        pr = Program()
        wreg = self.qregs_array_alloc(pr, 1, n, "wreg", str, qregs_properties)
        pr.apply(
            qregs_init.initialize_qureg_given_bitstring(bitstring,
                                                        little_endian=False),
            wreg,
        )
        qregs1s = self.qregs_array_alloc(pr, weight, m, "qregs1s", int,
                                         qregs_properties)
        self.qregs_ancillae_array_noalloc(
            1, m, "qregs1s_add", qregs1s[-1].start + qregs1s[-1].length, str,
            qregs_properties)
        qregs0s = self.qregs_array_alloc(pr, n - weight, m, "qregs0s", int,
                                         qregs_properties)
        self.qregs_ancillae_array_noalloc(
            1, m, "qregs0s_add", qregs0s[-1].start + qregs0s[-0].length, str,
            qregs_properties)
        # ancillary register of unknown size, catch all
        self.qregs_ancillae_array_noalloc(
            -1, -1, "anc", qregs0s[-1].start + qregs0s[-0].length + m, str,
            qregs_properties)
        state = CircuitTestCase.get_rprogram_regs(
            pr, qregs_properties.,
            [cuccaro_arith.adder, cuccaro_arith.subtractor])
        self.print_rprogram_regs_from_rprogram_states(state, reg_name_to_size)
        input()
        # qfun = bix.bix_fixed_weight_indexes(n, weight, index_start_at_one)
        pr.apply(bix_func, wreg, *qregs1s, *qregs0s)
        circ = pr.to_circ(link=[cuccaro_arith.adder, cuccaro_arith.subtractor])
        obtained = self.run_and_get_bitstring_for_reversible(
            circ, reg_name_to_slice)

        expected = {
            "wreg": bitstring,
            "qregs1s": exp_ones,
            "qregs1s_add": "0" * m,
            "qregs0s": exp_zeros,
            "qregs0s_add": "0" * m,
        }
        self.extract_and_check_named_regs(obtained, reg_name_to_slice,
                                          expected)

    @parameterized.expand([
        "0101",
        #0 "1001",
        # "0001",
        # "1000",
        # "1101",
        # "10011",
        # "11011",
        # "0001101",
        # "1111000",
        # "10110100",
        # "11001011",
        # "111001011",
    ])
    @unittest.skipUnless(CircuitTestCase.REVERSIBLE_ON,
                         "Only enabled with reversible simulation")
    def test_bix_indexes(self, bitstring):
        pass

    def _test_bix_indexes(self, bitstring):
        n = len(bitstring)
        weight = bitstring.count("1")
        for index_start_at_one in (False, True):
            add = 1 if index_start_at_one else 0
            m = (n + 1).bit_count()
            onesexp = [
                bin(i + add)[2:].zfill(m) for i, j in enumerate(bitstring)
                if j == "1"
            ]
            zerosexp = [
                bin(i + add)[2:].zfill(m) for i, j in enumerate(bitstring)
                if j == "0"
            ]
            qfun = bix.bix_fixed_weight_indexes(n, weight, index_start_at_one)
            self._run_test_bix(
                n,
                m,
                weight,
                bitstring,
                onesexp,
                zerosexp,
                qfun,
            )

    @parameterized.expand([
        ("0101", [0, 1, 2, 3]),
        ("0101", [2, 8, 10, 12]),
        ("0001", [3, 5, 7, 9]),
        ("1000", [1, 4, 6, 8]),
        ("1101", [0, 2, 5, 11]),
        ("10011", [1, 3, 8, 9, 11]),
        ("11011", [0, 6, 7, 13, 14]),
        ("0001101", [2, 3, 4, 6, 9, 10, 11]),
        ("1111000", [0, 1, 2, 3, 10, 12, 14]),
        ("10110100", [1, 2, 4, 7, 8, 9, 11, 15]),
        ("11001011", [0, 1, 5, 6, 8, 10, 11, 13]),
        ("111001011", [0, 1, 2, 6, 7, 9, 11, 13, 14]),
    ])
    @unittest.skipUnless(CircuitTestCase.REVERSIBLE_ON,
                         "Only enabled with reversible simulation")
    def test_bix_fixed_weight_elems(self, bitstring, elems):
        n = len(bitstring)
        assert len(bitstring) == len(elems)
        m = max(elems).bit_length()
        onesexp = [
            bin(elems[i])[2:].zfill(m) for i, j in enumerate(bitstring)
            if j == "1"
        ]
        zerosexp = [
            bin(elems[i])[2:].zfill(m) for i, j in enumerate(bitstring)
            if j == "0"
        ]
#         self._test_bix_fixed_weight_common_elems(bitstring, elems)

    @parameterized.expand([
        # 3 rows, select middle row
        ("010", np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])),
        ("001", np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])),
        ("100", np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])),

        # 4 rows, select outer rows
        ("1001", np.array([[10, 20], [30, 40], [50, 60], [70, 80]])),

        # 5 rows, select middle three
        ("01110", np.array([[1], [2], [3], [4], [5]])),

        # 2 rows, select all
        ("10", np.array([[100, 101, 102], [200, 201, 202]])),

        # 6 rows, select alternating rows
        ("101010", np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11,
                                                                       12]])),
    ])
    @unittest.skipUnless(CircuitTestCase.REVERSIBLE_ON,
                         "Only enabled with reversible simulation")
    def test_bix_fixed_weight_matrix(self, bitstring, matrix):
        n = len(bitstring)
        rows, cols = len(matrix), len(matrix[0])
        LOGGER.debug("n %d, rows %d, cols %d", n, rows, cols)
        assert rows == n, "bitstring should have same length of rows, got n %d, rows %d" % (
            n, rows)
        matrix_flat = [int(i) for i in chain.from_iterable(matrix)]

        m = max(matrix_flat).bit_length()
        LOGGER.debug("m %d", m)
        onesexp = [
            matrix[idx].tolist() for idx, val in enumerate(bitstring)
            if val == "1"
        ]
        zerosexp = [
            matrix[idx].tolist() for idx, val in enumerate(bitstring)
            if val == "0"
        ]


#         self._test_bix_fixed_weight_common_matrix(bitstring, matrix)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARNING,
        format='%(filename)s %(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger("qatext.qroutines.bix").setLevel(logging.DEBUG)
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    test = BixTestCase("test_bix_indexes")
    test.setUpClass()
    test.setUp()  # optional, if you have a setUp method
    test.REVERSIBLE_ON = True
    # Example bitstring and matrix
    bitstring = "0101"
    # Manually call the test method
    test._test_bix_indexes(bitstring)
    test.tearDown()
    test.tearDownClass()

    # bitstring = "010"
    # matrix = [
    #     [1, 2],
    #     [4, 5],
    #     [7, 8],
    # ]
    # matrix = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]
    # bitstring, matrix = ("01110", np.array([[1], [2], [3], [4], [5]]))
    # bitstring, matrix = ("1001",
    #                      np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11],
    #                                [12, 13, 14, 15]]))
