import numpy as np
import pytest
import qat.lang.AQASM.classarith
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.qint import QInt
from qat.lang.qpus.classical_qpu import ClassicalQPU
from qatext.qpus.reversible import RProgram
from qatext.qroutines import qregs_init as qregs
from qatext.qroutines.datastructure.sliding_sort_array import sliding_sorted_array
from qatext.utils.bits.conversion import get_int_from_bitarray, get_ints_from_bitarray

QPU = ClassicalQPU()

def _inner_state_test(pr, reg_names_to_range, reg_names_to_sizes):
    circ = pr.to_circ(link=[qat.lang.AQASM.classarith], inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr.rregs = reg_names_to_range
    res= rpr.get_result_by_name()
    print(reg_names_to_range)
    for qreg_name in reg_names_to_range:
        n, m = reg_names_to_sizes[qreg_name]
        if n == -1:
            val = res[qreg_name]
        else:
            val = get_ints_from_bitarray(res[qreg_name], n, m, False)
        print(f"{qreg_name}-> {val}, {res[qreg_name]}")
    return


@pytest.mark.parametrize(
    "values, max_value, value_to_insert",
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
        # Insertion of existing max value
        ([1, 2], 3, 3),
    ])
def test_insertion(values, max_value, value_to_insert):
    m = max_value
    # last one is the empty cell, used as temporary
    n = len(values) + 1
    pr = Program()
    qr_x = pr.qalloc(m)

    range_start = 0
    reg_names_to_range: dict[str, range] = {
        'x': range(range_start, m),
    }
    # tuple is (n, m), with n the number of elements in the bitstring, m the
    # size of each element
    reg_names_to_sizes: dict[str, tuple[int, int]] = {
        'x': (1, m)
    }
    range_start += m

    qfun = qregs.initialize_qureg_given_int(value_to_insert, m, False)
    pr.apply(qfun, qr_x)
    # _inner_state_test(pr, reg_names_to_range, reg_names_to_sizes)
    # return

    qrs_data = []
    for i, value in enumerate(values):
        qrs_data.append(pr.qalloc(m, QInt))
        qfun = qregs.initialize_qureg_given_int(value, m, False)
        # qf_tmp = qcs.int_to_bit_enc(m, value, True)
        pr.apply(qfun, qrs_data[i])
    # last one, empty
    qrs_data.append(pr.qalloc(m, QInt))
    reg_names_to_range['a'] = range(range_start, range_start + n * m)
    reg_names_to_sizes['a'] = (n, m)
    range_start += n * m
    # _inner_state_test(pr, reg_names_to_range, reg_names_to_sizes)
    # return

    qrs_data_i = []
    for _ in range(n):
        qrs_data_i.append(pr.qalloc(m, QInt))
    reg_names_to_range['a1'] = range(range_start, range_start + n * m)
    reg_names_to_sizes['a1'] = (n, m)
    range_start += n * m

    qrs_data_ii = pr.qalloc(n, QInt)
    reg_names_to_range['a2'] = range(range_start, range_start + n)
    reg_names_to_sizes['a2'] = (n, 1)
    range_start += n
    # _inner_state_test(pr, reg_names_to_range, reg_names_to_sizes)
    # return

    qf = sliding_sorted_array(m, n)
    # ancillary, don't know the sizes
    reg_names_to_range['ax'] = range(range_start, range_start + 199)
    reg_names_to_sizes['ax'] = (-1, 1)

    pr.apply(qf, qr_x, *qrs_data, *qrs_data_i, *qrs_data_ii)
    # _inner_state_test(pr, reg_names_to_range, reg_names_to_sizes)
    # return

    circ = pr.to_circ(link=[qat.lang.AQASM.classarith], inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr.rregs = reg_names_to_range
    res = rpr.get_result_by_name()

    x_val = get_int_from_bitarray(res['x'], False)
    a_vals = get_ints_from_bitarray(res['a'], n, m, False)
    ai_vals = get_ints_from_bitarray(res['a1'], n, m, False)
    aii_vals = get_ints_from_bitarray(res['a2'], n, 1, False)
    ax_val =  res['ax']
    # print(x_val, a_vals, ai_vals, aii_vals)

    values.append(value_to_insert)
    assert (x_val == value_to_insert)
    assert (tuple(sorted(values)) == a_vals)
    assert (ai_vals == tuple(0 for _ in range(n)))
    assert (aii_vals == tuple(0 for _ in range(n)))
    assert (any(ax_val) == False)


@pytest.mark.parametrize("values, value_to_delete", [
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
def test_deletion(values, value_to_delete):
    m = int(np.ceil(np.log2(max(values) + 1)))
    # last one is the empty cell
    n = len(values)
    pr = Program()

    qr_x = pr.qalloc(m)
    # qf_tmp = qcs.int_to_bit_enc(m, value_to_delete, True)
    qfun = qregs.initialize_qureg_given_int(value_to_delete, m, False)
    pr.apply(qfun, qr_x)

    qrs_data = []
    for i, value in enumerate(values):
        qrs_data.append(pr.qalloc(m, QInt))
        # qf_tmp = qcs.int_to_bit_enc(m, value, True)
        qfun = qregs.initialize_qureg_given_int(value, m, False)
        pr.apply(qfun, qrs_data[i])
    # last one, empty
    qrs_data.append(pr.qalloc(m, QInt))

    qrs_data_i = []
    for _ in range(n):
        qrs_data_i.append(pr.qalloc(m, QInt))
    qrs_data_ii = pr.qalloc(n, QInt)

    qf = sliding_sorted_array(m, n).dag()
    pr.apply(qf, qr_x, *qrs_data, *qrs_data_i, *qrs_data_ii)

    circ = pr.to_circ(link=[qat.lang.AQASM.classarith], inline=True)

    # res = QPU.submit(circ.to_job())
    # for sample in res:
    #     print(sample)
    reg_names_to_range: dict[str, range] = {
        'x': range(0, m),
        'a': range(m, m + n * m),
        'a1': range(m + n * m, m + 2 * n * m),
        'a2': range( m + 2 * n * m,  m + 2 * n * m + n),
        'ax': range( m + 2 * n * m + n,  m + 2 * n * m + n + 100),
    }
    circ = pr.to_circ(link=[qat.lang.AQASM.classarith], inline=True)
    rpr = RProgram.circuit_to_rprogram(circ)
    rpr.rregs = reg_names_to_range
    res = rpr.get_result_by_name()
    # for name, bitstring in zip(reg_names_to_range, res):
    #     print(name, bitstring)
    # for name, bitstring in zip(reg_names_to_range, res):
    #     _n = 1 if name == 'x' else n
    #     _m = 1 if name == 'ax' or name ==  'a2' else m
    #     print(name, get_ints_from_bitstring(_n, _m, bitstring))

    x_val = get_int_from_bitarray(res['x'], False)
    a_vals = get_ints_from_bitarray(res['a'], n, m, False)
    ai_vals = get_ints_from_bitarray(res['a1'], n, m, False)
    aii_vals = get_ints_from_bitarray(res['a2'], n, 1, False)
    ax_val =  res['ax']
    values.remove(value_to_delete)
    assert (tuple(sorted(values)) == a_vals[:-1])
    assert (x_val == value_to_delete)
    assert (a_vals[-1] == 0)
    assert (ai_vals == tuple(0 for _ in range(n)))
    assert (aii_vals == tuple(0 for _ in range(n)))
    assert (any(ax_val) == False)

if __name__ == '__main__':
    print(f"to insert [1, 2, 4], m = 4, x = 3")
    test_insertion([1, 2, 4], 4, 3)
    # print(f"to delete [0, 1, 2, 3], m = 4, x = 2")
    # test_deletion([0, 1, 2, 3], 2)
