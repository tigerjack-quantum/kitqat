from test.common_pytest import (REVERSIBLE_ON, REVERSIBLE_ON_REASON,
                                CircuitTestHelpers)

import pytest
import qat.lang.AQASM.classarith
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import get_states_from_program_wrapper
from qatext.qroutines.datastructure.arrays import contains
from qatext.qroutines.qregs_init import initialize_qureg_given_int
from qatext.utils.bits.conversion import (get_int_from_bitarray,
                                          get_ints_from_bitarray)
from qatext.utils.qatmgmt.program import ProgramWrapper


# @pytest.mark.usefixtures("setup_simulator", "setup_logger")
class TestArrays(CircuitTestHelpers):

    @pytest.mark.parametrize(
        "element, array, expected",
        [
            (3, [1, 2, 3, 4], True),
            (0, [1, 2, 3, 4], False),
            (5, [1, 2, 3, 4, 5], True),
            (6, [1, 2, 3, 4, 7, 9], False),
            # unordered
            (6, [3, 0, 1, 2, 7, 9], False),
            (6, [3, 0, 1, 2, 7, 6], True),
        ])
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_element_in_array_no_reps(self, element, array, expected):
        n = len(array)
        m = max(array).bit_length()
        prw = ProgramWrapper(Program())
        qreg_elem = prw.qarray_alloc(1, m, "element", int)[0]
        qarray = prw.qarray_alloc(n, m, "array", int)
        qbit_out = prw.qarray_alloc(1, 1, "out", str)[0][0]
        prw.qarray_noalloc(None, None, "anc", None, str, True)

        qroutw = initialize_qureg_given_int(element, m, False)
        prw.apply(qroutw, qreg_elem)

        for qreg_val, val in zip(qarray, array):
            qroutw = initialize_qureg_given_int(val, m, False)
            prw.apply(qroutw, qreg_val)

        qroutw = contains(n, m, False)
        prw.apply(qroutw, qreg_elem, *qarray, qbit_out)
        # print(inspect_state_reversible_program(prw, [qat.lang.AQASM.classarith]))

        states = get_states_from_program_wrapper(prw,
                                                 [qat.lang.AQASM.classarith])
        array_vals = get_ints_from_bitarray(states["array"], n, m, False)
        assert list(array_vals) == array
        elem_val = get_int_from_bitarray(states["element"], False)
        assert elem_val == element
        out_val = bool(get_int_from_bitarray(states["out"], False))
        assert out_val == expected
        anc_val = states['anc']
        assert (any(anc_val) == False)
        # print(qroutw.arity)

    @pytest.mark.parametrize("element, array, expected", [
        (3, [1, 2, 1, 3], True),
        (1, [1, 2, 1, 3], True),
        (0, [1, 2, 1, 2], False),
        (0, [3, 1, 2, 4, 2], False),
        (0, [3, 1, 0, 4, 0], True),
        (4, [1, 2, 4, 4, 7, 9], True),
    ])
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_element_in_array_reps(self, element, array, expected):
        n = len(array)
        m = max(array).bit_length()
        prw = ProgramWrapper(Program())
        qreg_elem = prw.qarray_alloc(1, m, "element", int)[0]
        qarray = prw.qarray_alloc(n, m, "array", int)
        qbit_out = prw.qarray_alloc(1, 1, "out", str)[0][0]
        prw.qarray_noalloc(None, None, "anc", None, str, True)

        qroutw = initialize_qureg_given_int(element, m, False)
        prw.apply(qroutw, qreg_elem)

        for qreg_val, val in zip(qarray, array):
            qroutw = initialize_qureg_given_int(val, m, False)
            prw.apply(qroutw, qreg_val)

        qroutw = contains(n, m, True)
        prw.apply(qroutw, qreg_elem, *qarray, qbit_out)
        # print(inspect_state_reversible_program(prw, [qat.lang.AQASM.classarith]))

        states = get_states_from_program_wrapper(prw,
                                                 [qat.lang.AQASM.classarith])
        array_vals = get_ints_from_bitarray(states["array"], n, m, False)
        assert list(array_vals) == array
        elem_val = get_int_from_bitarray(states["element"], False)
        assert elem_val == element
        out_val = bool(get_int_from_bitarray(states["out"], False))
        assert out_val == expected
        anc_val = states['anc']
        assert (any(anc_val) == False)
        # print(qroutw.arity)


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(filename)s %(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger("qatext.qroutines.datastructure.arrays").setLevel(
        logging.DEBUG)
    logging.getLogger(
        "qsg.permutations.reversible.indexes.generation").setLevel(
            logging.DEBUG)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    test = TestArrays()
    # Pytest fixture setup
    test.logger = logging.getLogger("manual-test")
    test.qpu = None  # or some dummy/mock QPU
    test.reversible_on = True

    test.test_element_in_array_no_reps(3, [1, 2, 3, 4], True)
    # 🔥 Runs the test
    print("Test ran successfully")
