# from qat.external.utils.qroutines.fake import fake_gate
from qat.external.utils.qroutines.linalg import gauss_jordan_isd as gji
from qat.external.utils.qroutines.linalg import matrix as qmatrix
from qat.lang.AQASM.program import Program
from qat.core.util import statistics
from numpy import argmax


def _prepare_circuit(r, n):
    pr = Program()
    qr_mat = pr.qalloc(r * n)
    qr_rows = qmatrix.get_rows_as_qubit_list(r, n, qr_mat)
    return pr, qr_rows


def _build_gje_circuit(r, n):
    pr, qregs_rows = _prepare_circuit(r, n)

    add_ancillae_n, swap_ancillae_n = gji.get_required_ancillae(r)
    swap_ancillae = pr.qalloc(swap_ancillae_n)
    add_ancillae = pr.qalloc(add_ancillae_n)
    rref_gate = gji.get_rref(r, n)
    pr.apply(rref_gate, qregs_rows, swap_ancillae, add_ancillae)
    return pr


def _get_max_depth_qbits(vec, qblist):
    maxd = 0
    for qb in qblist:
        curr = vec[qb]
        if curr > maxd:
            maxd = curr
    return maxd


def _compute_depth(cr):
    vec = [0] * cr.nbqbits
    # for op in pr.op_list:
    for op in cr:
        maxd = _get_max_depth_qbits(vec, op.qbits)
        # print(maxd)
        for qb in op.qbits:
            vec[qb] = maxd + 1
    return max(vec), argmax(vec), vec


def main():
    for r in range(3, 20):
        pr = _build_gje_circuit(r, r)
        cr = pr.to_circ()
        sts = statistics(cr)
        depth, depth_i, vec = _compute_depth(cr)

        print(f"r: {r}, CCNOT: {sts['gates']['C-C-X']}, depth: {depth}, max depth qbit: {depth_i}/{cr.nbqbits}")
        if r == 3:
            print(vec)


if __name__ == '__main__':
    main()
