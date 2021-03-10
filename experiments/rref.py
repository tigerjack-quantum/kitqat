import numpy as np
from qat.core.console import display
from qat.core.util import statistics
from qat.external.utils.qroutines import qregs_init, rref
from qat.lang.AQASM.program import Program
# from qat.qpus import LinAlg
from qat.pylinalg import PyLinalg as LinAlg
from sympy import Matrix
from copy import deepcopy

from isdclassic.utils import rectangular_codes_hardcoded as rch

import itertools

def _prepare_circuit(matrix):
    pr = Program()
    n_rows, n_cols = matrix.shape
    qregs_rows = []
    for row_idx in range(n_rows):
        # qregs_rows.append(qregs_init.ini)
        qreg = pr.qalloc(n_cols)
        qrout = qregs_init.initialize_qureg_given_bitarray(
            matrix[row_idx, :], qreg, False)
        pr.apply(qrout, qreg)
        qregs_rows.append(qreg)

    qbit_range = set(q.index for qreg in qregs_rows for q in qreg)
    return pr, qregs_rows, qbit_range


def test_simple():
    # Should be ok
    # mat = np.array([[0, 1, 1], [1, 0, 1], [0, 0, 1]])
    # Should fail
    # mat = np.array([[0, 1, 1], [0, 0, 1], [0, 1, 1]])
    # Should be long
    # mat = np.array([[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]])
    # Non square mat test
    # mat = np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]])
    # Another strange test
    mat = np.array([[1, 0, 0, 1, 0], [0, 0, 0, 0, 0], [1, 1, 0, 1, 1]], )
    pr, qregs_rows, qbit_range = _prepare_circuit(mat)

    nrows, ncols = mat.shape
    nsquare = min(nrows, ncols)
    # aouts = []
    # bouts = []

    add_ancillae = pr.qalloc(nsquare * (nsquare - 1))
    swap_ancillae = pr.qalloc(int(len(add_ancillae) / 2))
    rref_gate = rref.get_rref(nrows, ncols)
    pr.apply(rref_gate, qregs_rows, swap_ancillae, add_ancillae)

    cr = pr.to_circ()
    print(statistics(cr))
    del cr

    print("Measured through cr.to_job(qubits=)")
    print(qregs_rows[0])
    print(qregs_rows[1])
    print(qregs_rows[2])
    # print("Measured through pr.measure")
    # print(swap_ancillae)
    # print(add_ancillae)
    # pr.measure(qbits=swap_ancillae)
    # pr.measure(qbits=add_ancillae)

    qpu = LinAlg()
    # qpu = Feynman()
    cr = pr.to_circ()
    print(statistics(cr))
    # print(f"n qubits = {cr.nbqbits}")
    res = qpu.submit(cr.to_job(qubits=qregs_rows))
    sample = res.raw_data[0]
    # print("sample")
    # print(sample)

    mat_rref = rref.build_rref_matrix_from_sample(sample, qbit_range,
                                                  mat.shape)
    print("original mat")
    print(mat)
    print("mat rref expected")
    print(Matrix(mat).rref())
    print("mat rrefobtained")
    print(mat_rref)

    u = rref.build_u_matrix_from_sample(sample, nsquare)
    if u is not None:
        print("u mat")
        print(u)
        print("double check: u * mat_original...")
        print(u @ mat % 2)
        print("... should be equal to mat_rref")
        print(mat_rref)

    # err = np.array([1, 1, 0, 1])
    err = np.random.randint(2, size=(mat.shape[1]))
    syn = mat @ err % 2

    syn_qreg = pr.qalloc(len(syn))
    qrout = qregs_init.initialize_qureg_given_bitarray(syn, syn_qreg, False)
    pr.apply(qrout, syn_qreg)
    # apply_ops_to_syndrome(swap_ancillae, add_ancillae, syn_qreg, pr, nsquare)
    qrout2 = rref.gate_same_ops_for_vector(nrows, ncols)
    pr.apply(qrout2, syn_qreg, swap_ancillae, add_ancillae)
    cr = pr.to_circ()
    res = qpu.submit(cr.to_job(qubits=[syn_qreg]))
    sample = res.raw_data[0]

    print("original syn")
    print(syn)
    syn_sig = mat_rref @ err % 2
    print("syn signed expected")
    print(syn_sig)
    print("obtained syn signed")
    print(sample.state.bitstring)


def test_s():
    mat = np.array([[0, 1, 1, 1], [1, 0, 0, 1], [0, 0, 1, 1]])
    # nsquare = min(mat.shape)
    err = np.array([1, 1, 0, 1])
    syn = mat @ err % 2

    pr = Program()
    swap_ancilla_n, add_ancilla_n = rref.get_required_ancillae(*mat.shape)
    add_ancilla = pr.qalloc(add_ancilla_n)
    swap_ancilla = pr.qalloc(swap_ancilla_n)
    syn_qreg = pr.qalloc(len(syn))
    qrout = qregs_init.initialize_qureg_given_bitarray(syn, syn_qreg, False)
    pr.apply(qrout, syn_qreg)
    # apply_ops_to_syndrome(swap_ancilla, add_ancilla, syn_qreg, pr, nsquare)
    qrout2 = rref.gate_same_ops_for_vector(*mat.shape)
    pr.apply(qrout2, swap_ancilla, add_ancilla, syn_qreg)
    cr = pr.to_circ()
    display(cr)
    qpu = LinAlg()
    res = qpu.submit(cr.to_job(qubits=[syn_qreg]))
    sample = res.raw_data[0]

    print(f"original syn {syn}")
    print(f"obtained syn {sample.state.bitstring}")


def test_isd():
    n, k, d, w = 4, 1, 4, 1
    h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
        n, k, d, w)

    qpu = LinAlg()
    for syn, err in zip(syndromes, errors):
        print("===")
        pr, qregs_rows, qbit_range = _prepare_circuit(h)
        swap_qr_n, add_qr_n = rref.get_required_ancillae(*h.shape)
        swap_qr = pr.qalloc(swap_qr_n)
        add_qr = pr.qalloc(add_qr_n)
        rref_gate = rref.get_rref(*h.shape)
        pr.apply(rref_gate, qregs_rows, swap_qr, add_qr)

        syn = h @ err % 2
        syn_qreg = pr.qalloc(len(syn))
        qrout = qregs_init.initialize_qureg_given_bitarray(
            syn, syn_qreg, False)
        pr.apply(qrout, syn_qreg)

        qrout2 = rref.gate_same_ops_for_vector(*h.shape)
        pr.apply(qrout2, syn_qreg, swap_qr, add_qr)

        cr = pr.to_circ()
        res = qpu.submit(cr.to_job(qubits=qregs_rows))
        sample = res.raw_data[0]
        h_rref = rref.build_rref_matrix_from_sample(sample, qbit_range,
                                                    h.shape)

        print("original h")
        print(h)
        print("h rref expected")
        print(Matrix(h).rref(pivots=False) % 2)
        print("h rrefobtained")
        print(h_rref)

        res = qpu.submit(cr.to_job(qubits=[syn_qreg]))
        sample = res.raw_data[0]
        print("original syn")
        print(syn)
        syn_sig = h_rref @ err % 2
        print("syn signed expected")
        print(syn_sig)
        print("obtained syn signed")
        syn_sig_obt = np.array(sample.state.bitstring)
        print(syn_sig_obt)
        np.testing.assert_array_equal(syn_sig_obt, syn_sig)


def test_subparts():
    n, k, d, w = 4, 1, 4, 1
    h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
        n, k, d, w)

    qpu = LinAlg()
    idx = np.random.choice(len(syndromes))
    print(f"index {idx}")
    for syn, err in zip(syndromes[idx], errors[idx]):
    # for i in itertools.combinations(range(h.shape[1]), h.shape[0]):
        print("===")
        pr, qregs_rows, qbit_range = _prepare_circuit(h)
        swap_qr_n, add_qr_n = rref.get_required_ancillae(*h.shape)
        swap_qr = pr.qalloc(swap_qr_n)
        add_qr = pr.qalloc(add_qr_n)
        rref_gate = rref.get_rref(*h.shape)
        pr.apply(rref_gate, qregs_rows, swap_qr, add_qr)
        syn = h @ err % 2
        syn_qreg = pr.qalloc(len(syn))
        qrout = qregs_init.initialize_qureg_given_bitarray(
            syn, syn_qreg, False)
        pr.apply(qrout, syn_qreg)
        qrout2 = rref.gate_same_ops_for_vector(*h.shape)
        pr.apply(qrout2, syn_qreg, swap_qr, add_qr)
        cr = pr.to_circ()
        res = qpu.submit(cr.to_job(qubits=qregs_rows))
        sample = res.raw_data[0]
        h_rref = rref.build_rref_matrix_from_sample(sample, qbit_range,
                                                    h.shape)

        print("original h")
        print(h)
        print("h rref expected")
        print(Matrix(h).rref(pivots=False) % 2)
        print("h rrefobtained")
        print(h_rref)

        res = qpu.submit(cr.to_job(qubits=[syn_qreg]))
        sample = res.raw_data[0]

        print("original syn")
        print(syn)
        syn_sig = h_rref @ err % 2
        print("syn signed expected")
        print(syn_sig)
        print("obtained syn signed")
        print(sample.state.bitstring)

def main():
    # test_simple()
    # test_s()
    test_isd()
    # test_subparts()


if __name__ == '__main__':
    main()
