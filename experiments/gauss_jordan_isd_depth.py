# from qat.external.utils.qroutines.fake import fake_gate
from qat.core.util import statistics
# from qat.external.utils.qroutines.linalg import gauss_jordan_isd as gji
from qat.external.utils.qroutines.linalg import gauss_jordan_isd_opt5 as gji5
from qat.external.utils.qroutines.linalg import matrix as qmatrix
from qat.lang.AQASM.program import Program

# from numpy import argmax
# from qat.core.console import display


def _prepare_circuit(r, n):
    pr = Program()
    qr_mat = pr.qalloc(r * n)
    qr_rows = qmatrix.get_rows_as_qubit_list(r, n, qr_mat)
    return pr, qr_rows


def _build_gje_circuit(r, n, gjmod, alg='prange'):
    pr, qregs_rows = _prepare_circuit(r, n)

    add_ancillae_n, swap_ancillae_n = gjmod.get_required_ancillae(r)
    swap_ancillae = pr.qalloc(swap_ancillae_n)
    add_ancillae = pr.qalloc(add_ancillae_n)
    skip_rightmost = alg=='prange'
    rref_gate = gjmod.get_rref(r, n, skip_rightmost)
    pr.apply(rref_gate, qregs_rows, swap_ancillae, add_ancillae)
    return pr


def _get_max_depth_qbits(vec, qblist):
    maxd = 0
    for qb in qblist:
        curr = vec[qb]
        if curr > maxd:
            maxd = curr
    return maxd


def _compute_depth(cr, include_intermediate=False):
    vec = [0] * cr.nbqbits
    # for op in pr.op_list:
    for op in cr:
        if include_intermediate:
            print(vec)
        maxd = _get_max_depth_qbits(vec, op.qbits)
        # print(maxd)
        for qb in op.qbits:
            vec[qb] = maxd + 1
    if include_intermediate:
        print(vec)
    m = max(vec)
    argmaxs = [i for i, j in enumerate(vec) if j == m]
    return m, argmaxs


def _trans_qbit_to_txt(r, qbits, gjmod):
    txts = []

    swap_ancillae_n, add_ancillae_n = gjmod.get_required_ancillae(r)
    # last element of matrix
    last = r * r - 1

    for qb in qbits:
        if qb > last:
            # ancilla
            if qb > last + swap_ancillae_n:
                # add_ancillae [last + swap_ancillae_n: +add_ancillae_n]
                idx = qb - last - swap_ancillae_n - 1
                txt = f"C[{idx}]"
            else:
                # swap_ancillae [last: last + swap_ancillae_n]
                idx = qb - last - 1
                txt = f"B[{idx}]"
        else:
            row = qb // r
            col = qb % r
            txt = f"H[{row},{col}]"
        txts.append(txt)
    return txts


def main():
    gjmod = gji
    # for r in range(3, 4):
    # for r in range(4, 5):
    # for r in range(20, 21):
    for r in range(25, 26):
        # pr = _build_gje_circuit(r, r, gjmod)
        pr = _build_gje_circuit(r, r+40, gjmod, alg='lee-brickell')
        cr = pr.to_circ(include_matrices=False)
        # display(cr, max_depth=2)
        sts = statistics(cr)
        # print(sts)
        ccnot_n = sts['gates'].get('C-C-X', 0) + sts['gates'].get('CCNOT', 0)
        depth, depth_i = _compute_depth(cr, include_intermediate=False)
        trans = _trans_qbit_to_txt(r, depth_i, gjmod)

        print(
            f"r: {r}, CCNOT: {ccnot_n}, depth: {depth}, max depth qbits: {depth_i}/{cr.nbqbits}, corresponding to {trans}"
        )


if __name__ == '__main__':
    main()
