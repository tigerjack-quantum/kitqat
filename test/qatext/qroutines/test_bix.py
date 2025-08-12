import logging
from itertools import chain
from test.common_pytest import (REVERSIBLE_ON, REVERSIBLE_ON_REASON,
                                CircuitTestHelpers)
from typing import TYPE_CHECKING

import pytest
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import (get_state_from_program,
                                    inspect_state_reversible_program)
from qatext.qroutines import bix, qregs_init
from qatext.qroutines.arith import cuccaro_arith
from qatext.utils.bits.conversion import get_bitstring_from_int
from qatext.qatmgmt.program import ProgramWrapper

if TYPE_CHECKING:
    from qatext.qatmgmt.program import QRegsProperties

LOGGER = logging.getLogger(__name__)


# @pytest.mark.usefixtures("setup_simulator", "setup_logger")
class TestBix(CircuitTestHelpers):

    def _extract_and_check_named_regs(
            self, bitstring, expected_map,
            qregs_properties: dict[str, 'QRegsProperties']):
        """Post-processing checks"""
        for name, expected in expected_map.items():
            bits = bitstring[qregs_properties[name].slic]
            assert bits == expected, "key %s, bits %s, expected %s" % (
                name, bits, expected)

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
        # qregs_properties: dict[str, QRegsProperties] = {}
        is_runtime = runtime_data is not None

        prw = ProgramWrapper(Program())
        wreg = prw.qarray_alloc(1, n, "wreg", str)
        prw.apply(
            qregs_init.initialize_qureg_given_bitstring(bitstring,
                                                        little_endian=False),
            wreg,
        )
        qregs_data = None
        if is_runtime:
            qregs_data = prw.qarray_alloc(
                n * cols,
                m,
                "qregs_data",
                int,
            )
            for i in range(n * cols):
                LOGGER.debug("qregs_data[%d] = %s", i, qregs_data[i])

                prw.apply(
                    qregs_init.initialize_qureg_given_int(runtime_data[i],
                                                          m,
                                                          little_endian=False),
                    *qregs_data[i])
        qregs1s = prw.qarray_alloc(
            weight * cols,
            m,
            "qregs1s",
            int,
        )
        prw.qarray_noalloc(
            weight,
            m,
            "qregs1s_bits",
            qregs1s[0].start,
            str,
        )
        qregs0s = prw.qarray_alloc(
            (n - weight) * cols,
            m,
            "qregs0s",
            int,
        )
        prw.qarray_noalloc(n - weight, m, "qregs0s_bits", qregs0s[0].start,
                           str)

        anc_start = qregs0s[-1].start + qregs0s[-1].length
        if has_support_registers:
            prw.qarray_noalloc(
                1,
                m,
                "qregs1s_add",
                anc_start,
                str,
            )
            anc_start += m
            LOGGER.debug("zeros will be rotated")
            prw.qarray_noalloc(
                1,
                m,
                "qregs0s_add",
                anc_start,
                str,
            )
            anc_start += m
        # ancillary register of unknown size, catch all
        prw.qarray_noalloc(None,
                           None,
                           "anc",
                           anc_start,
                           str,
                           unknown_size=True)
        LOGGER.debug("Applying bix_func of arity %d", bix_func.arity)
        if is_runtime:
            prw.apply(bix_func, wreg, qregs_data, *qregs1s, *qregs0s)
        else:
            prw.apply(bix_func, wreg, *qregs1s, *qregs0s)
        LOGGER.debug(
            "%s",
            inspect_state_reversible_program(
                prw, [cuccaro_arith.adder, cuccaro_arith.subtractor]))

        obtained = get_state_from_program(
            prw, [cuccaro_arith.adder, cuccaro_arith.subtractor])

        expected = {
            "wreg": bitstring,
            "qregs1s": exp_ones,
            "qregs0s": exp_zeros,
        }
        if has_support_registers:
            expected["qregs1s_add"] = "0" * m
            expected["qregs0s_add"] = "0" * m
        self._extract_and_check_named_regs(obtained, expected,
                                           prw._qregnames_to_properties)

    @pytest.mark.parametrize("bitstring", [
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
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
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
    @pytest.mark.parametrize("bitstring, elements", [
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
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_bix_data_diff_compile_time(self, bitstring, elements):
        self._test_bix_data_diff_compile_time(bitstring, elements)

    def _test_bix_data_diff_compile_time(self, bitstring, elements):
        LOGGER.debug("bitstring %s", bitstring)
        n = len(bitstring)
        weight = bitstring.count("1")
        LOGGER.debug("Len %d, weight %d", n, weight)
        assert len(bitstring) == len(elements)
        m = max(elements).bit_length()
        onesexp = "".join([
            get_bitstring_from_int(elements[i], m)
            for i, j in enumerate(bitstring) if j == "1"
        ])
        zerosexp = "".join([
            get_bitstring_from_int(elements[i], m)
            for i, j in enumerate(bitstring) if j == "0"
        ])
        LOGGER.debug("onesexp %s", onesexp)
        LOGGER.debug("zerosexp %s", zerosexp)
        qfun = bix.bix_data_diff_compile_time(n, m, weight, elements)
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

    @pytest.mark.parametrize("bitstring, elements", [
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
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_bix_data_compile_time(self, bitstring, elements):
        self._test_bix_data_compile_time(bitstring, elements)

    def _test_bix_data_compile_time(self, bitstring, elements):
        LOGGER.debug("bitstring %s", bitstring)
        n = len(bitstring)
        weight = bitstring.count("1")
        LOGGER.debug("Len %d, weight %d", n, weight)
        assert len(bitstring) == len(elements)
        m = max(elements).bit_length()
        onesexp = "".join([
            get_bitstring_from_int(elements[i], m)
            for i, j in enumerate(bitstring) if j == "1"
        ])
        zerosexp = "".join([
            get_bitstring_from_int(elements[i], m)
            for i, j in enumerate(bitstring) if j == "0"
        ])
        LOGGER.debug("onesexp %s", onesexp)
        LOGGER.debug("zerosexp %s", zerosexp)
        qfun = bix.bix_data_compile_time(n, m, weight, elements)
        LOGGER.debug("Got qfun with arity %d", qfun.arity)
        self._run_test_bix(
            n,
            m,
            weight,
            bitstring,
            onesexp,
            zerosexp,
            qfun,
            has_support_registers=False,
        )

    @pytest.mark.parametrize(
        "bitstring, matrix",
        [
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
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
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

    @pytest.mark.parametrize(
        "bitstring, elements",
        [
            # select middle row
            ("010", [0, 1, 2]),
            ("001", [0, 1, 2]),
            ("100", [0, 1, 2]),

            # select outer rows
            ("1001", [10, 20, 30, 40]),

            # select middle three
            ("01110", [1, 2, 3, 4, 5]),

            # select
            ("10", [100, 101]),

            # select alternating rows
            ("101010", [5, 15, 30, 45, 75, 120]),
        ])
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_bix_data_runtime(self, bitstring, elements):
        self._test_bix_data_runtime(bitstring, elements)

    def _test_bix_data_runtime(self, bitstring, elements):
        LOGGER.debug("bitstring %s", bitstring)
        n = len(bitstring)
        weight = bitstring.count("1")
        LOGGER.debug("Len %d, weight %d", n, weight)
        m = max(elements).bit_length()
        LOGGER.debug("m %d", m)
        onesexp = "".join([
            get_bitstring_from_int(elements[idx], m, False)
            for idx, val in enumerate(bitstring) if val == "1"
        ])
        zerosexp = "".join([
            get_bitstring_from_int(elements[idx], m, False)
            for idx, val in enumerate(bitstring) if val == "0"
        ])
        LOGGER.debug("onesexp %s", onesexp)
        LOGGER.debug("zerosexp %s", zerosexp)

        qfun = bix.bix_data_runtime(n, m, weight)
        LOGGER.debug("Got qfun with arity %d", qfun.arity)
        self._run_test_bix(
            n,
            m,
            weight,
            bitstring,
            onesexp,
            zerosexp,
            qfun,
            has_support_registers=False,
            runtime_data=elements,
        )

    @pytest.mark.parametrize(
        "bitstring, matrix",
        [
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
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
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


# if __name__ == '__main__':
#     logging.basicConfig(
#         level=logging.WARNING,
#         format='%(filename)s %(asctime)s - %(levelname)s - %(message)s')
#     logging.getLogger("qatext.qroutines.bix").setLevel(logging.DEBUG)
#     logging.getLogger("test.common_circuit").setLevel(logging.DEBUG)
#     logging.getLogger(__name__).setLevel(logging.DEBUG)
#     # test = BixTestCase("test_bix_indexes")
#     test = BixTestCase()
#     test.setUpClass()
#     test.setUp()  # optional, if you have a setUp method
#     test.REVERSIBLE_ON = True
#     # Example bitstring and matrix
#     # bitstring = "0001"
#     # test._test_bix_indexes(bitstring)

#     # bitstring, elements = ("0101", [2, 8, 10, 12])
#     # test._test_bix_elements(bitstring, elements)

#     bitstring, array = (
#         "010",
#         [2, 5, 8],
#     )
#     test._test_bix_data_runtime(bitstring, array)

#     # bitstring, matrix = ("010", [
#     #     [1, 2],
#     #     [4, 5],
#     #     [7, 8],
#     # ])
#     # test._test_bix_matrix(bitstring, matrix)
#     test.tearDown()
#     test.tearDownClass()
