import numpy as np
from qat.core.console import display
from qat.core.util import statistics
from kitqat.utils.qatmgmt.qbits import \
    add_name_to_qbits_following_pattern
# from kitqat.qroutines.fake import fake_gate
from kitqat.qroutines.linalg import gauss_jordan_isd4 as gji
from kitqat.qroutines.linalg import matrix as qmatrix
from qat.lang.AQASM.program import Program
# from qat.qpus import LinAlg
from qat.pylinalg import PyLinalg as LinAlg
from sympy import Matrix


def _prepare_circuit(matrix, init_matrix=True, add_fake_gate=False):
    pr = Program()
    r, n = matrix.shape
    qr_mat = pr.qalloc(r * n)
    qr_rows = qmatrix.get_rows_as_qubit_list(r, n, qr_mat)

    if add_fake_gate:
        rows = {}
        for i, row in enumerate(qr_rows):
            rows[f'row{i}'] = row
        add_name_to_qbits_following_pattern(pr, rows)
        # display(pr.to_circ())
    if init_matrix:
        qg_mat = qmatrix.initialize_qureg_to_binary_matrix(matrix)
        pr.apply(qg_mat, qr_mat)
    qbit_range = set(q.index for qrow in qr_rows for q in qrow)
    return pr, qr_rows, qbit_range


def test_simple(mat):
    pr, qregs_rows, qbit_range = _prepare_circuit(mat,
                                                  init_matrix=True,
                                                  add_fake_gate=False)
    r, n = mat.shape

    swap_ancillae_n, add_ancillae_n = gji.get_required_ancillae(r)
    swap_ancillae = pr.qalloc(swap_ancillae_n)
    # add_ancillae = pr.qalloc(add_ancillae_n)
    add_name_to_qbits_following_pattern(pr, {
        # 'cadd': add_ancillae,
        'swap': swap_ancillae
    })
    rref_gate = gji.get_rref(r, n, False, -1)
    pr.apply(rref_gate, qregs_rows, swap_ancillae)

    cr = pr.to_circ()
    # display(cr, max_depth=2)
    # display(cr)
    print(statistics(cr))
    # return
    # del cr

    print("Measured through cr.to_job(qubits=)")

    qpu = LinAlg()
    res = qpu.submit(cr.to_job(qubits=qbit_range))
    sample = res.raw_data[0]
    # print("sample")
    # print(sample)

    mat_rref = qmatrix.build_matrix_from_sample(sample, qbit_range, mat.shape)
    print("original mat")
    print(mat)
    print("mat rref expected")
    print(Matrix(mat).rref())
    print("mat rref obtained")
    print(mat_rref)


def main():
    # Should be ok
    for mat, msg in (
        (np.array([[0, 1, 1], [1, 0, 1], [0, 0, 1]]), "ok"),
        (np.array([[0, 1, 1], [0, 0, 1], [0, 1, 1]]), "should fail"),
        # (np.array([[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1],
        #            [0, 1, 1, 0]]), "should be long"),
        (np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1,
                                                1]]), "non square test"),
        (np.array([[1, 0, 0, 1, 0], [0, 0, 0, 0, 0], [1, 1, 0, 1,
                                                      1]]), "strange, fail"),
    ):
        test_simple(mat)
        print(msg)
        print("*" * 80)


if __name__ == '__main__':
    main()
