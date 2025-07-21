import logging
import unittest
from itertools import chain
from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import inspect_rprogram_state
from qatext.qroutines import bix, qregs_init
from qatext.qroutines.arith import cuccaro_arith
from qatext.utils.bits.conversion import get_bitstring_from_int
from qatext.utils.qatmgmt.qbits import (QRegsProperties,
                                        qregs_ancillae_array_noalloc,
                                        qregs_array_alloc)

LOGGER = logging.getLogger(__name__)


class BixTestCase(CircuitTestCase):

    def _extract_and_check_named_regs(self, bitstring, expected_map,
                                      qregs_properties: dict[str,
                                                             QRegsProperties]):
        """Post-processing checks"""
        for name, expected in expected_map.items():
            bits = bitstring[qregs_properties[name].slic]
            self.assertEqual(
                bits, expected,
                "key %s, bits %s, expected %s" % (name, bits, expected))

    def _run_test_bix(
            self,
            n,
            m,
            weight,
            bitstring,
            exp_ones,
            exp_zeros,
            bix_func,
            cols=1,  # Make sense only for matrices
            has_support_registers=True,  # bix_matrix, for example, doesn't have them
            runtime_data=None,  # If it is applied to bix_runtime, it must be != None
    ):
        qregs_properties: dict[str, QRegsProperties] = {}
        is_runtime = runtime_data is not None

        pr = Program()
        wreg = qregs_array_alloc(pr, 1, n, "wreg", str, qregs_properties)
        pr.apply(
            qregs_init.initialize_qureg_given_bitstring(bitstring,
                                                        little_endian=False),
            wreg,
        )
        qregs_data = None
        if is_runtime:
            qregs_data = qregs_array_alloc(pr, n * cols, m, "qregs_data", int,
                                           qregs_properties)
            for i in range(n * cols):
                LOGGER.debug("qregs_data[%d] = %s", i, qregs_data[i])

                pr.apply(
                    qregs_init.initialize_qureg_given_int(runtime_data[i],
                                                          m,
                                                          little_endian=False),
                    *qregs_data[i])
        qregs1s = qregs_array_alloc(pr, weight * cols, m, "qregs1s", int,
                                    qregs_properties)
        qregs_ancillae_array_noalloc(weight, m, "qregs1s_bits",
                                     qregs1s[0].start, str, qregs_properties)
        qregs0s = qregs_array_alloc(pr, (n - weight) * cols, m, "qregs0s", int,
                                    qregs_properties)
        qregs_ancillae_array_noalloc(n - weight, m, "qregs0s_bits",
                                     qregs0s[0].start, str, qregs_properties)

        anc_start = qregs0s[-1].start + qregs0s[-1].length
        if has_support_registers:
            qregs_ancillae_array_noalloc(1, m, "qregs1s_add", anc_start, str,
                                         qregs_properties)
            anc_start += m
            LOGGER.debug("zeros will be rotated")
            qregs_ancillae_array_noalloc(1, m, "qregs0s_add", anc_start, str,
                                         qregs_properties)
            anc_start += m
        # ancillary register of unknown size, catch all
        qregs_ancillae_array_noalloc(None,
                                     None,
                                     "anc",
                                     anc_start,
                                     str,
                                     qregs_properties,
                                     unknown_size=True)
        LOGGER.debug("Applying bix_func of arity %d", bix_func.arity)
        if is_runtime:
            pr.apply(bix_func, wreg, qregs_data, *qregs1s, *qregs0s)
        else:
            pr.apply(bix_func, wreg, *qregs1s, *qregs0s)
        LOGGER.debug(
            "%s",
            inspect_rprogram_state(
                pr, qregs_properties,
                [cuccaro_arith.adder, cuccaro_arith.subtractor]))

        circ = pr.to_circ(link=[cuccaro_arith.adder, cuccaro_arith.subtractor])
        obtained = self.run_and_get_bitstring_for_reversible(
            circ, qregs_properties)

        expected = {
            "wreg": bitstring,
            "qregs1s": exp_ones,
            "qregs0s": exp_zeros,
        }
        if has_support_registers:
            expected["qregs1s_add"] = "0" * m
            expected["qregs0s_add"] = "0" * m
        self._extract_and_check_named_regs(obtained, expected,
                                           qregs_properties)

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
    def test_bix_indexes(self, bitstring):
        self._test_bix_indexes(bitstring)

    def _test_bix_indexes(self, bitstring):
        LOGGER.debug("bitstring %s", bitstring)
        n = len(bitstring)
        weight = bitstring.count("1")
        LOGGER.debug("Len %d, weight %d", n, weight)
        for index_start_at_one in (False, True):
            add = 1 if index_start_at_one else 0
            m = (n - 1 + add).bit_length()
            LOGGER.debug("add %d, m %d (index_start_at_one is %s)", add, m,
                         index_start_at_one)
            onesexp = "".join([
                get_bitstring_from_int(i + add, m)
                for i, j in enumerate(bitstring) if j == "1"
            ])
            zerosexp = "".join([
                get_bitstring_from_int(i + add, m)
                for i, j in enumerate(bitstring) if j == "0"
            ])
            LOGGER.debug("onesexp %s", onesexp)
            LOGGER.debug("zerosexp %s", zerosexp)
            qfun = bix.bix_indexes_compile_time(n, weight, index_start_at_one)
            LOGGER.debug("Got qfun with arity %d", qfun.arity)
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
    def test_bix_elems(self, bitstring, elems):
        self._test_bix_elems(bitstring, elems)

    def _test_bix_elems(self, bitstring, elems):
        LOGGER.debug("bitstring %s", bitstring)
        n = len(bitstring)
        weight = bitstring.count("1")
        LOGGER.debug("Len %d, weight %d", n, weight)
        assert len(bitstring) == len(elems)
        m = max(elems).bit_length()
        onesexp = "".join([
            get_bitstring_from_int(elems[i], m)
            for i, j in enumerate(bitstring) if j == "1"
        ])
        zerosexp = "".join([
            get_bitstring_from_int(elems[i], m)
            for i, j in enumerate(bitstring) if j == "0"
        ])
        LOGGER.debug("onesexp %s", onesexp)
        LOGGER.debug("zerosexp %s", zerosexp)
        qfun = bix.bix_data_compile_time(n, m, weight, elems)
        LOGGER.debug("Got qfun with arity %d", qfun.arity)
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
        # 3 rows, select middle row
        ("010", [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]),
        ("001", [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]),
        ("100", [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]),

        # 4 rows, select outer rows
        ("1001", [[10, 20], [30, 40], [50, 60], [70, 80]]),

        # 5 rows, select middle three
        ("01110", [[1], [2], [3], [4], [5]]),

        # 2 rows, select all
        ("10", [[100, 101, 102], [200, 201, 202]]),

        # 6 rows, select alternating rows
        ("101010", [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]]),
    ])
    @unittest.skipUnless(CircuitTestCase.REVERSIBLE_ON,
                         "Only enabled with reversible simulation")
    def test_bix_matrix(self, bitstring, matrix):
        self._test_bix_matrix(bitstring, matrix)

    def _test_bix_matrix(self, bitstring, matrix):
        LOGGER.debug("bitstring %s", bitstring)
        n = len(bitstring)
        weight = bitstring.count("1")
        LOGGER.debug("Len %d, weight %d", n, weight)
        rows, cols = len(matrix), len(matrix[0])
        LOGGER.debug("n %d, rows %d, cols %d", n, rows, cols)
        assert rows == n, "bitstring should have same length of rows, got n %d, rows %d" % (
            n, rows)
        matrix_flat = [int(i) for i in chain.from_iterable(matrix)]
        m = max(matrix_flat).bit_length()
        LOGGER.debug("m %d", m)
        onesexp_rows = [
            matrix[idx] for idx, val in enumerate(bitstring) if val == "1"
        ]
        zerosexp_rows = [
            matrix[idx] for idx, val in enumerate(bitstring) if val == "0"
        ]
        LOGGER.debug("onesexp %s", onesexp_rows)
        LOGGER.debug("zerosexp %s", zerosexp_rows)
        onesexp = "".join(
            get_bitstring_from_int(i, m)
            for i in chain.from_iterable(onesexp_rows))
        zerosexp = "".join(
            get_bitstring_from_int(i, m)
            for i in chain.from_iterable(zerosexp_rows))

        qfun = bix.bix_matrix_compile_time(rows, cols, m, weight, matrix_flat)
        LOGGER.debug("Got qfun with arity %d", qfun.arity)
        self._run_test_bix(
            n,
            m,
            weight,
            bitstring,
            onesexp,
            zerosexp,
            qfun,
            cols=cols,
            has_support_registers=False,
        )

    @parameterized.expand([
        # 3 rows, select middle row
        ("010", [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]),
        ("001", [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]),
        ("100", [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]),

        # 4 rows, select outer rows
        ("1001", [[10, 20], [30, 40], [50, 60], [70, 80]]),

        # 5 rows, select middle three
        ("01110", [[1], [2], [3], [4], [5]]),

        # 2 rows, select all
        ("10", [[100, 101, 102], [200, 201, 202]]),

        # 6 rows, select alternating rows
        ("101010", [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]]),
    ])
    @unittest.skipUnless(CircuitTestCase.REVERSIBLE_ON,
                         "Only enabled with reversible simulation")
    def test_bix_matrix_runtime(self, bitstring, matrix):
        self._test_bix_matrix_runtime(bitstring, matrix)

    def _test_bix_matrix_runtime(self, bitstring, matrix):
        LOGGER.debug("bitstring %s", bitstring)
        n = len(bitstring)
        weight = bitstring.count("1")
        LOGGER.debug("Len %d, weight %d", n, weight)
        rows, cols = len(matrix), len(matrix[0])
        LOGGER.debug("n %d, rows %d, cols %d", n, rows, cols)
        assert rows == n, "bitstring should have same length of rows, got n %d, rows %d" % (
            n, rows)
        matrix_flat = [int(i) for i in chain.from_iterable(matrix)]
        m = max(matrix_flat).bit_length()
        LOGGER.debug("m %d", m)
        onesexp_rows = [
            matrix[idx] for idx, val in enumerate(bitstring) if val == "1"
        ]
        zerosexp_rows = [
            matrix[idx] for idx, val in enumerate(bitstring) if val == "0"
        ]
        LOGGER.debug("onesexp %s", onesexp_rows)
        LOGGER.debug("zerosexp %s", zerosexp_rows)
        onesexp = "".join(
            get_bitstring_from_int(i, m)
            for i in chain.from_iterable(onesexp_rows))
        zerosexp = "".join(
            get_bitstring_from_int(i, m)
            for i in chain.from_iterable(zerosexp_rows))

        qfun = bix.bix_matrix_runtime(rows, cols, m, weight)
        LOGGER.debug("Got qfun with arity %d", qfun.arity)
        self._run_test_bix(
            n,
            m,
            weight,
            bitstring,
            onesexp,
            zerosexp,
            qfun,
            cols=cols,
            has_support_registers=False,
            runtime_data=matrix_flat,
        )


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARNING,
        format='%(filename)s %(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger("qatext.qroutines.bix").setLevel(logging.DEBUG)
    logging.getLogger("test.common_circuit").setLevel(logging.DEBUG)
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    # test = BixTestCase("test_bix_indexes")
    test = BixTestCase()
    test.setUpClass()
    test.setUp()  # optional, if you have a setUp method
    test.REVERSIBLE_ON = True
    # Example bitstring and matrix
    # bitstring = "0001"
    # test._test_bix_indexes(bitstring)

    # bitstring, elems = ("0101", [2, 8, 10, 12])
    # test._test_bix_elems(bitstring, elems)

    bitstring, matrix = ("010", [
        [1, 2],
        [4, 5],
        [7, 8],
    ])
    test._test_bix_matrix(bitstring, matrix)
    test.tearDown()
    test.tearDownClass()
