# from qat.external.utils.qroutines.fake import fake_gate
from qat.core.util import statistics
from qat.external.utils.qroutines.linalg import gauss_jordan_isd as gji
# from qat.external.utils.qroutines.linalg import gauss_jordan_isd_opt5 as gji5
from qat.external.utils.qroutines.linalg import matrix as qmatrix
from qat.lang.AQASM.program import Program

# from numpy import argmax
from qat.core.console import display


def _prepare_circuit(r, n):
    pr = Program()
    qr_mat = pr.qalloc(r * n)
    qr_rows = qmatrix.get_rows_as_qubit_list(r, n, qr_mat)
    return pr, qr_rows


def _build_gje_circuit(r, n, gjmod, alg='prange'):
    pr, qregs_rows = _prepare_circuit(r, n)

    skip_rightmost = alg == 'prange'
    add_ancillae_n, swap_ancillae_n = gjmod.get_required_ancillae(r)
    swap_ancillae = pr.qalloc(swap_ancillae_n)
    add_ancillae = pr.qalloc(add_ancillae_n)
    rref_gate = gjmod.get_rref(r, n, skip_rightmost, -1)
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
    dic = {}
    # for op in pr.op_list
    for idx, op in enumerate(cr):
        # if include_intermediate:
        #     print(op)
        maxd = _get_max_depth_qbits(vec, op.qbits)
        # print(maxd)
        for qb in op.qbits:
            vec[qb] = maxd + 1
        if include_intermediate:
            dic[f"{idx}_{op.gate}_{op.qbits}"] = maxd + 1
        #     print(vec)
    m = max(vec)
    argmaxs = [i for i, j in enumerate(vec) if j == m]
    return m, argmaxs, dic


def _trans_qbit_to_txt(r, n, qbits, gjmod, skip_rightmost):
    txts = []

    swap_ancillae_n, add_ancillae_n = gjmod.get_required_ancillae(r)
    # last element of matrix
    last = r * n - 1

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
            row = qb // n
            col = qb % n
            txt = f"H[{row},{col}]"
        txts.append(txt)
    return txts


def main():
    gjmod = gji
    # for r in range(3, 4):
    # for r in range(4, 5):
    # for r in range(5, 6):
    # for r in range(7, 8):
    # for r in range(15, 16):
    for r in range(20, 21):
    # for r in range(25, 26):
    # for r in range(35, 36):
        n = r
        n = 2 * r
        # n = r + 40
        alg = 'prange'
        # alg = 'lee'
        pr = _build_gje_circuit(r, n, gjmod, alg)
        cr = pr.to_circ(include_matrices=False)
        # display(cr, max_depth=2)
        sts = statistics(cr)
        # print(sts)
        ccnot_n = sts['gates'].get('C-C-X', 0) + sts['gates'].get('CCNOT', 0)
        cnot_n = sts['gates'].get('C-X', 0) + sts['gates'].get('CNOT', 0)
        depth, depth_i, dic = _compute_depth(cr, include_intermediate=True)
        # depth, depth_i, dic = _compute_depth(cr, include_intermediate=False)
        trans = _trans_qbit_to_txt(r, n, depth_i, gjmod, alg == 'prange')

        for op, dep in dic.items():
            print(op, dep)

        print(
            f"r: {r}, n: {n}, CNOT: {cnot_n}, CCNOT: {ccnot_n}, depth: {depth}, max depth qbits: {depth_i}/{cr.nbqbits}, corresponding to {trans}"
        )

        #################################
        # QLM only
        # from qat.nnize.metrics import DurationMetric
        # from qat.plugins import Graphopt
        # from qat.core.simutil import optimize_circuit
 
        # metric = DurationMetric()
        # metric.set_gate_time({"-DEFAULT-": 1})
        # print(f"Depth of circuit: {-metric(cr)}")
        # metric.minimize_overall_time()
        # print(f"Depth of circuit: {-metric(cr)}")

        # cr_opt = optimize_circuit(cr, Graphopt(verbose=True))
        # print(statistics(cr_opt))
        # display(cr_opt)
        # depth, depth_i = _compute_depth(cr_opt, include_intermediate=False)
        # print(depth, depth_i)

 


if __name__ == '__main__':
    main()
