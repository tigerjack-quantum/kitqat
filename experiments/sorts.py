import functools
import itertools
import operator

import numpy as np
from qat.external.utils.qroutines import qregs_init
from qat.external.utils.qroutines import sorting_network as sn
from qat.external.utils.qroutines.linalg import matrix as qmatrix
from qat.lang.AQASM.program import Program
from qat.pylinalg.service import PyLinalg

QPU = PyLinalg()


def _prepare_circuit(matrix):
    pr = Program()
    nrows, ncols = matrix.shape
    qreg_mat = pr.qalloc(nrows * ncols)
    mat_init = qmatrix.initialize_qureg_to_binary_matrix(matrix)
    pr.apply(mat_init, qreg_mat)

    # qregs_rows = qmatrix.get_rows_as_qubit_list(*matrix.shape, qreg_mat)
    # qregs_cols = qmatrix.get_columns_as_qubit_list(*matrix.shape, qreg_mat)
    qbit_rows_idx = qmatrix.get_columns_as_index_list(*matrix.shape, qreg_mat)
    qbit_range = functools.reduce(operator.concat, qbit_rows_idx)
    return pr, qreg_mat, qbit_range
    # return pr, qreg_mat, qregs_rows, qregs_cols, qbit_rows_idx, qbit_range


def bla2(string):
    n = len(string)
    data = sn.get_pattern_sorter(n)
    print(data)


def bla3(s):
    pr = Program()
    n = len(s)
    data = sn.get_pattern_sorter(n)
    lines = pr.qalloc(data['n_lines'])
    comps = pr.qalloc(data['n_comps'])

    init = qregs_init.initialize_qureg_given_bitstring(s, True)
    pr.apply(init, lines)

    sort_net = sn.build_gate_sorter(data)
    pr.apply(sort_net, lines, comps)
    cr = pr.to_circ()
    # display(cr, max_depth=3)

    res = QPU.submit(cr.to_job())
    print(res.raw_data[0].state)


def tada(h, s):
    # pr, qregs_rows, qregs_cols, qbit_rows_idx, qbit_range = _prepare_circuit(h)
    pr, qreg_mat, qbit_range = _prepare_circuit(h)

    # data = sn.get_pattern_sorter(len(s))
    data = qmatrix.move_columns_end_data(*h.shape)
    comb = pr.qalloc(data['n_lines'])
    comps = pr.qalloc(data['n_comps'])

    # Initialize the combination
    init = qregs_init.initialize_qureg_given_bitstring(s, True)
    pr.apply(init, comb)

    # sort_net = sn.build_gate_sorter(data)_
    # pr.apply(sort_net, comb, comps)

    # sort_mat = sn.build_gate_sn_cols(
    #     h.shape[0], pattern)
    move_cols = qmatrix.move_columns_end_gate(data)
    pr.apply(move_cols, qreg_mat, comb, comps)
    # display(pr.to_circ(), max_depth=2)

    print("qubit count")
    print(pr.qbit_count)
    cr = pr.to_circ()
    res = QPU.submit(cr.to_job())
    sample = res.raw_data[0]
    print("sample")
    print(sample)
    print(sample.state)

    # mat_rref = rref.build_rref_matrix_from_sample(sample, qbit_range, h.shape)
    mat_rref = qmatrix.build_matrix_from_sample(sample, qbit_range, h.shape)
    s_sort = ''.join([sample.state.bitstring[qb.index] for qb in comb])
    print("original matrix")
    print(h)
    print(f"combination vector {s}")
    print(f"sorted combination vector {s_sort}")
    comp_str = ''.join([sample.state.bitstring[qb.index] for qb in comps])
    print(f"comparator bits {comp_str}")
    print("permuted matrix")
    print(mat_rref)


def main():
    # bla2("01001")

    h = np.random.randint(2, size=(3, 4))
    # h = np.array([[1, 0, 1], [1, 1, 0], [1, 0, 0]])
    # h = np.array([[1, 0], [1, 1]])
    for comb in itertools.combinations(range(h.shape[1]), 1):
        lis = ['0'] * h.shape[1]
        for i in comb:
            lis[i] = '1'
        st = ''.join(lis)
        tada(h, st)
        print("---")

    # for s in ("01", "10", "0110", "1010", "1000", "1011"):
    #     print(f"original {s}")
    #     pr = bla3(s)


if __name__ == '__main__':
    main()
