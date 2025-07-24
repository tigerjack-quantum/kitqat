from test.common_pytest import (REVERSIBLE_ON, REVERSIBLE_ON_REASON,
                                CircuitTestHelpers)

import numpy as np
import pytest
import qat.lang.AQASM.classarith
# from parameterized import parameterized
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import get_states_from_program_wrapper
from qatext.qroutines import qregs_init as qregs
from qatext.qroutines.datastructure.sliding_sort_array import delete, insert
from qatext.utils.bits.conversion import (get_int_from_bitarray,
                                          get_ints_from_bitarray)
from qatext.utils.qatmgmt.program import ProgramWrapper


@pytest.mark.usefixtures("setup_simulator", "setup_logger")
class TestQroutineSlidingSort(CircuitTestHelpers):

    @pytest.mark.parametrize(
        "values, max_bits, value_to_insert",
        [
            # Insert in the middle
            ([1, 2, 4], 4, 3),
            ([2, 4, 6], 7, 3),
            # Insert at the beginning
            ([2, 3, 4], 5, 1),
            # Insert at the end
            ([1, 3, 4], 5, 5),
            # Insert duplicate in the middle
            ([1, 2, 3], 3, 2),
            # Insert duplicate at the end
            ([1, 2, 3], 3, 3),
            # Insert into empty list
            ([], 5, 2),
            # Insert below lower bound
            ([1, 2, 3], 3, 0),
            # Insert above upper bound
            ([1, 2, 3], 3, 4),
            # Single-element list, insert before
            ([3], 3, 2),
            # Single-element list, insert after
            ([2], 4, 3),
            # 0-element list, insert after
            ([], 4, 3),
            # Insertion of existing max value
            ([1, 2], 3, 3),
        ])
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_insertion(self, values, max_bits, value_to_insert):
        m = max_bits
        # last one is the empty cell, used as temporary
        n = len(values) + 1
        prw = ProgramWrapper(Program())
        # qregs_properties: dict[str, QRegsProperties] = {}
        qr_x = prw.qarray_alloc(1, m, "x", int)
        qfun = qregs.initialize_qureg_given_int(value_to_insert, m, False)
        prw.apply(qfun, qr_x)

        qrs_data = prw.qarray_alloc(n, m, "a", int)
        for i, value in enumerate(values):
            qfun = qregs.initialize_qureg_given_int(value, m, False)
            prw.apply(qfun, qrs_data[i])
        prw.qarray_noalloc(n, m, "a1",
                                qrs_data[-1].start + qrs_data[-1].length, int)
        prw.qarray_noalloc(
            n,
            1,
            "a2",
            qrs_data[-1].start + qrs_data[-1].length + n * m,
            int,
        )
        prw.qarray_noalloc(None,
                                None,
                                "anc",
                                qrs_data[-1].start + qrs_data[-1].length +
                                n * m + n,
                                str,
                                unknown_size=True)

        qf = insert(n, m)
        prw.apply(qf, qr_x, *qrs_data)

        res = get_states_from_program_wrapper(prw, [qat.lang.AQASM.classarith])
        # self.print_rprogram_regs_from_rprogram_states(states, qregs_properties)

        x_val = get_int_from_bitarray(res['x'], False)
        a_vals = get_ints_from_bitarray(res['a'], n, m, False)
        ai_vals = get_ints_from_bitarray(res['a1'], n, m, False)
        aii_vals = get_ints_from_bitarray(res['a2'], n, 1, False)
        ax_val = res['anc']
        # print(x_val, a_vals, ai_vals, aii_vals)

        values.append(value_to_insert)
        assert (x_val == value_to_insert)
        assert (tuple(sorted(values)) == a_vals)
        assert (ai_vals == tuple(0 for _ in range(n)))
        assert (aii_vals == tuple(0 for _ in range(n)))
        assert (any(ax_val) == False)

    @pytest.mark.parametrize(
        "values, value_to_delete",
        [
            ([0, 1, 2, 3], 0),
            ([0, 1, 2, 3], 3),
            ([1, 2, 3, 4], 3),
            ([2, 4, 5, 6], 5),
            ([1, 2, 3, 4], 1),
            ([1, 2, 3, 4], 3),
            ([1, 2, 3, 4], 2),
            ([1, 2, 3, 4], 4),
            ([2, 3, 4], 3),
            ([2, 4], 2),
            ([4], 4),
            # Delete from beginning
            ([0, 1, 2, 3], 0),
            ([1, 2, 3, 4], 1),
            # Delete from end
            ([0, 1, 2, 3], 3),
            ([1, 2, 3, 4], 4),
            # Delete from middle
            ([1, 2, 3, 4], 2),
            ([2, 4, 5, 6], 5),
            ([2, 3, 4], 3),
            # Delete unique value
            ([4], 4),
            # Delete when multiple identical elements
            ([1, 2, 2, 3], 2),
            ([2, 2, 2], 2),
            # Delete from single-element list
            ([3], 3),
            # These cases are not handled by the sliding sorted array
            # # Value not in list
            # ([1, 2, 3, 4], 5),
            # ([0, 1, 2], -1),
            # # Empty list
            # ([], 1),
        ])
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_deletion(self, values, value_to_delete):
        m = int(np.ceil(np.log2(max(values) + 1)))
        # last one is the empty cell
        n = len(values)
        prw = ProgramWrapper(Program())

        qr_x = prw.qarray_alloc(1, m, "x", int)
        qfun = qregs.initialize_qureg_given_int(value_to_delete, m, False)
        prw.apply(qfun, qr_x)

        qrs_data = prw.qarray_alloc(n, m, "a", int)
        for i, value in enumerate(values):
            qfun = qregs.initialize_qureg_given_int(value, m, False)
            prw.apply(qfun, qrs_data[i])
        prw.qarray_noalloc(n, m, "a1",
                                qrs_data[-1].start + qrs_data[-1].length, int)
        prw.qarray_noalloc(
            n,
            1,
            "a2",
            qrs_data[-1].start + qrs_data[-1].length + n * m,
            int,
        )
        prw.qarray_noalloc(None,
                                None,
                                "anc",
                                qrs_data[-1].start + qrs_data[-1].length +
                                n * m + n,
                                str,
                                unknown_size=True)

        qf = delete(n, m)
        prw.apply(qf, qr_x, *qrs_data)

        # circ = pr.to_circ(link=[qat.lang.AQASM.classarith], inline=True)
        # rpr = RProgram.circuit_to_rprogram(circ)
        # rpr.rregs = reg_names_to_slice
        # res = rpr.get_result_by_name()
        res = get_states_from_program_wrapper(prw, [qat.lang.AQASM.classarith])

        x_val = get_int_from_bitarray(res['x'], False)
        a_vals = get_ints_from_bitarray(res['a'], n, m, False)
        ai_vals = get_ints_from_bitarray(res['a1'], n, m, False)
        aii_vals = get_ints_from_bitarray(res['a2'], n, 1, False)
        ax_val = res['anc']
        values.remove(value_to_delete)
        assert (tuple(sorted(values)) == a_vals[:-1])
        assert (x_val == value_to_delete)
        assert (a_vals[-1] == 0)
        assert (ai_vals == tuple(0 for _ in range(n)))
        assert (aii_vals == tuple(0 for _ in range(n)))
        assert (any(ax_val) == False)


# if __name__ == '__main__':
#     # print(f"to insert [1, 2, 4], m = 4, x = 3")
#     # test_insertion([1, 2, 4], 4, 3)
#     # print(f"to insert [2, 4, 6], m = 7, x = 3")
#     # test_insertion([2, 4, 6], 7, 3)
#     print(f"to insert [1, 2, 4, 7], m = 4, x = 3")
#     test_insertion([1, 2, 4, 7], 3, 3)
#     # print(f"to delete [0, 1, 2, 3], m = 4, x = 2")
#     # test_deletion([0, 1, 2, 3], 2)
