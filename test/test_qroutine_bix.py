import itertools
import logging
import unittest
from itertools import chain
from math import ceil, log2
from test.common_circuit import CircuitTestCase

import numpy as np
from parameterized import parameterized
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import RProgram
from qatext.qroutines import bix, qregs_init
from qatext.qroutines.arith import cuccaro_arith
from qatext.utils.bits.conversion import get_ints_from_bitstring

LOGGER = logging.getLogger(__name__)
#


class BixTestCase(CircuitTestCase):

    def _test_bix_fixed_weight_common(self, bitstring, index_start_at_one):
        n = len(bitstring)
        # the additional + 1 is required since we want indexes starting from 1
        # to n (and not the traditional 0 to n-1)
        # add should be 0 for not idx_start_at_one
        add = 1 if index_start_at_one else 0
        l2n = int(ceil(log2(n + add)))
        onesexp = [
            bin(i + add)[2:].zfill(l2n) for i, j in enumerate(bitstring)
            if j == "1"
        ]
        zerosexp = [
            bin(i + add)[2:].zfill(l2n) for i, j in enumerate(bitstring)
            if j == "0"
        ]
        weight = len(onesexp)
        reg_name_to_slice = {}
        reg_name_to_size = {}

        pr = Program()
        wreg = pr.qalloc(n)
        reg_name_to_slice["wreg"] = slice(wreg.start, wreg.length)
        reg_name_to_size["wreg"] = (n, 1)
        oregs = []
        zregs = []
        for i in range(weight):
            qr = pr.qalloc(l2n)
            oregs.append(qr)
            reg_name_to_slice[f"oregs_{i}"] = slice(qr.start,
                                                    qr.start + qr.length)
        for i in range(n - weight):
            qr = pr.qalloc(l2n)
            zregs.append(qr)
            reg_name_to_slice[f"zregs_{i}"] = slice(qr.start,
                                                    qr.start + qr.length)

        pr.apply(
            qregs_init.initialize_qureg_given_bitstring(bitstring,
                                                        little_endian=False),
            wreg,
        )

        qfun = bix.bix_fixed_weight_indexes(n, weight, index_start_at_one)
        self.assertEqual(qfun.arity, n * l2n + n)
        pr.apply(qfun, wreg, *oregs, *zregs)

        circ = pr.to_circ(link=[cuccaro_arith.adder, cuccaro_arith.subtractor])
        # circ = pr.to_circ(link=[tkk_arith.adder])

        obtained = None
        if self.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(circ, reg_name_to_slice)
            obtained = rpr.rbits.to01()
        else:
            res = self.qpu.submit(circ.to_job())
            counts = len(res)
            self.assertEqual(counts, 1)
            for sample in res:
                if self.SIMULATOR == "linalg":
                    self.assertEqual(sample.probability, 1)
                obtained = sample.state.bitstring
        ones = []
        zeros = []
        assert obtained is not None
        for k, v in reg_name_to_slice.items():
            if k.startswith("oregs_"):
                ones.append(obtained[v.start:v.stop])
            elif k.startswith("zregs_"):
                zeros.append(obtained[v.start:v.stop])

        self.assertEqual(obtained[wreg.start:wreg.length], bitstring)
        for obt, exp in itertools.chain(zip(ones, onesexp),
                                        zip(zeros, zerosexp)):
            self.assertEqual(obt, exp)

        ancillae_start = zregs[-1].start + zregs[-1].length
        for i in obtained[ancillae_start:]:
            self.assertEqual(i, "0")

    def _test_bix_fixed_weight_common_elems(self, bitstring, elems):
        n = len(bitstring)
        m = max(elems).bit_length()
        # the additional + 1 is required since we want indexes starting from 1
        # to n (and not the traditional 0 to n-1)
        # add should be 0 for not idx_start_at_one
        # add = 1 if index_start_at_one else 0
        onesexp = [
            bin(elems[i])[2:].zfill(m) for i, j in enumerate(bitstring)
            if j == "1"
        ]
        zerosexp = [
            bin(elems[i])[2:].zfill(m) for i, j in enumerate(bitstring)
            if j == "0"
        ]
        weight = len(onesexp)
        reg_name_to_slice = {}
        reg_name_to_size = {}

        pr = Program()
        wreg = pr.qalloc(n)
        reg_name_to_slice[f"wreg"] = slice(wreg.start, wreg.length)
        reg_name_to_size["wreg"] = (n, 1)
        oregs = []
        zregs = []
        for _ in range(weight):
            qr = pr.qalloc(m)
            oregs.append(qr)
        reg_name_to_slice["oregs"] = slice(oregs[0].start,
                                           oregs[-1].start + oregs[-1].length)
        reg_name_to_size["oregs"] = (weight, m)

        for _ in range(n - weight):
            qr = pr.qalloc(m)
            zregs.append(qr)
        reg_name_to_slice["zregs"] = slice(zregs[0].start,
                                           zregs[-1].start + zregs[-1].length)
        reg_name_to_size["zregs"] = (n - weight, m)

        reg_name_to_slice["oregs_add"] = slice(
            reg_name_to_slice['zregs'].stop,
            reg_name_to_slice['zregs'].stop + m)
        reg_name_to_size["oregs_add"] = (1, m)
        reg_name_to_slice["zregs_add"] = slice(
            reg_name_to_slice['zregs'].stop + m,
            reg_name_to_slice['zregs'].stop + 2 * m)
        reg_name_to_size["zregs_add"] = (1, m)

        reg_name_to_slice['anc'] = slice(zregs[-1].start + zregs[-1].length,
                                         None)
        reg_name_to_size['anc'] = (-1, -1)

        pr.apply(
            qregs_init.initialize_qureg_given_bitstring(bitstring,
                                                        little_endian=False),
            wreg,
        )
        qfun = bix.bix_fixed_weight_data(n, m, weight, elems)

        self.assertEqual(qfun.arity, n * m + n)
        pr.apply(qfun, wreg, *oregs, *zregs)
        # self.print_rprogram_regs(pr, reg_name_to_slice, reg_name_to_size, [cuccaro_arith.adder, cuccaro_arith.subtractor])

        circ = pr.to_circ(link=[cuccaro_arith.adder, cuccaro_arith.subtractor])
        # circ = pr.to_circ(link=[tkk_arith.adder])

        obtained = None
        if self.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(circ, reg_name_to_slice)
            obtained = rpr.rbits.to01()
        else:
            res = self.qpu.submit(circ.to_job())
            counts = len(res)
            self.assertEqual(counts, 1)
            for sample in res:
                if self.SIMULATOR == "linalg":
                    self.assertEqual(sample.probability, 1)
                obtained = sample.state.bitstring
        ones = []
        zeros = []
        assert obtained is not None

        for k, slic in reg_name_to_slice.items():
            if k == 'wreg':
                val = obtained[slic]
                self.assertEqual(val, bitstring)
            elif k == 'anc':
                val = obtained[slic]
                self.assertFalse(any(map(lambda x: x == '1', val)))
            else:
                _n, _m = reg_name_to_size[k]
                val = get_ints_from_bitstring(obtained[slic], _n, _m, False)
                if k == 'oregs':
                    ones = list(val)
                elif k == 'zregs':  # necessarily zregs
                    zeros = list(val)
                elif k == 'oregs_add':
                    self.assertEqual(len(val), 1)
                    self.assertEqual(val[0], 0)
                elif k == 'zregs_add':
                    self.assertEqual(len(val), 1)
                    self.assertEqual(val[0], 0)
        for obt, exp in itertools.chain(zip(ones, onesexp),
                                        zip(zeros, zerosexp)):
            self.assertEqual(obt, int(exp, 2))

    def _test_bix_fixed_weight_common_matrix(self, bitstring, matrix):
        LOGGER.debug("bitstring %s", bitstring)
        LOGGER.debug("matrix")
        LOGGER.debug(matrix)
        n = len(bitstring)
        rows, cols = len(matrix), len(matrix[0])
        LOGGER.debug("n %d, rows %d, cols %d", n, rows, cols)
        assert rows == n, "bitstring should have same length of rows, got n %d, rows %d" % (
            n, rows)
        matrix_flat = [int(i) for i in chain.from_iterable(matrix)]

        m = max(matrix_flat).bit_length()
        LOGGER.debug("m %d", m)
        onesexp = [
            matrix[idx].tolist() for idx, val in enumerate(bitstring) if val == "1"
        ]
        zerosexp = [
            matrix[idx].tolist() for idx, val in enumerate(bitstring) if val == "0"
        ]
        LOGGER.debug("onesexp")
        LOGGER.debug(onesexp)
        LOGGER.debug("zerosexp")
        LOGGER.debug(zerosexp)

        weight = len(onesexp)
        reg_name_to_slice = {}
        reg_name_to_size = {}

        pr = Program()
        wreg = pr.qalloc(n)
        reg_name_to_slice[f"wreg"] = slice(wreg.start, wreg.length)
        reg_name_to_size["wreg"] = (n, 1)
        omatrix = []
        zmatrix = []
        for _ in range(weight):
            for _ in range(cols):
                qr = pr.qalloc(m)
                omatrix.append(qr)
        reg_name_to_slice["omatrix"] = slice(
            omatrix[0].start, omatrix[-1].start + omatrix[-1].length)
        reg_name_to_size["omatrix"] = (weight * cols, m)

        for _ in range(n - weight):
            for _ in range(cols):
                qr = pr.qalloc(m)
                zmatrix.append(qr)
        reg_name_to_slice["zmatrix"] = slice(
            zmatrix[0].start, zmatrix[-1].start + zmatrix[-1].length)
        reg_name_to_size["zmatrix"] = ((n - weight) * cols, m)

        LOGGER.debug(reg_name_to_slice)
        LOGGER.debug(reg_name_to_size)

        reg_name_to_slice['anc'] = slice(
            zmatrix[-1].start + zmatrix[-1].length, None)
        reg_name_to_size['anc'] = (-1, -1)

        pr.apply(
            qregs_init.initialize_qureg_given_bitstring(bitstring,
                                                        little_endian=False),
            wreg,
        )
        qfun = bix.bix_matrix(n, cols, m, weight, matrix_flat)

        self.assertEqual(qfun.arity, rows * cols * m + n)
        pr.apply(qfun, wreg, *omatrix, *zmatrix)
        # self.print_rprogram_regs(pr, reg_name_to_slice, reg_name_to_size, [cuccaro_arith.adder, cuccaro_arith.subtractor])

        circ = pr.to_circ(link=[cuccaro_arith.adder, cuccaro_arith.subtractor])
        # circ = pr.to_circ(link=[tkk_arith.adder])

        obtained = None
        if self.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(circ, reg_name_to_slice)
            obtained = rpr.rbits.to01()
        else:
            res = self.qpu.submit(circ.to_job())
            counts = len(res)
            self.assertEqual(counts, 1)
            for sample in res:
                if self.SIMULATOR == "linalg":
                    self.assertEqual(sample.probability, 1)
                obtained = sample.state.bitstring
        ones = []
        zeros = []
        assert obtained is not None
        LOGGER.debug("Len obtained %d", len(obtained))

        for k, slic in reg_name_to_slice.items():
            if k == 'wreg':
                val = obtained[slic]
                LOGGER.debug("wreg %s", val)
                self.assertEqual(val, bitstring)
            elif k == 'anc':
                val = obtained[slic]
                LOGGER.debug("anc %s", val)
                self.assertFalse(any(map(lambda x: x == '1', val)))
            else:
                _n, _m = reg_name_to_size[k]
                val = get_ints_from_bitstring(obtained[slic], _n, _m, False)
                if k == 'omatrix':
                    # reshaping to submatrix
                    ones = [
                        list(val[i * cols:(i + 1) * cols])
                        for i in range(weight)
                    ]
                    LOGGER.debug(ones)
                elif k == 'zmatrix':
                    zeros = [
                        list(val[i * cols:(i + 1) * cols])
                        for i in range(n - weight)
                    ]
                    LOGGER.debug(zeros)
        for obt, exp in itertools.chain(zip(ones, onesexp),
                                        zip(zeros, zerosexp)):
            self.assertEqual(obt, exp)

    @parameterized.expand([
        "0101",
        "1001",
        "0001",
        "1000",
        "1101",
        "10011",
        "11011",
        "0001101",
        "1111000",
        "10110100",
        "11001011",
        "111001011",
    ])
    @unittest.skipUnless(CircuitTestCase.REVERSIBLE_ON,
                         "Only enabled with reversible simulation")
    def test_bix_fixed_weight_large(self, bitstring):
        for index_start_at_one in (False, True):
            self._test_bix_fixed_weight_common(bitstring, index_start_at_one)

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
        self._test_bix_fixed_weight_common_elems(bitstring, elems)

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
        self._test_bix_fixed_weight_common_matrix(bitstring, matrix)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARNING,
        format='%(filename)s %(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger("qatext.qroutines.bix").setLevel(logging.DEBUG)
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    test = BixTestCase()
    test.setUpClass()
    test.setUp()  # optional, if you have a setUp method
    test.REVERSIBLE_ON = True
    # Example bitstring and matrix
    # bitstring = "101"
    # bitstring = "010"
    # matrix = [
    #     [1, 2],
    #     [4, 5],
    #     [7, 8],
    # ]
    # matrix = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]
    # bitstring, matrix = ("01110", np.array([[1], [2], [3], [4], [5]]))
    bitstring, matrix = ("1001", np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]]))

    # Manually call the test method
    test._test_bix_fixed_weight_common_matrix(bitstring, matrix)
    test.tearDown()
    test.tearDownClass()
