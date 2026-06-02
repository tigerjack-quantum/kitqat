# from kitqat.qroutines.fake import fake_gate
from qat.core.util import statistics

# from kitqat.qroutines.linalg import gauss_jordan_isd as gji
# from kitqat.qroutines.linalg import gauss_jordan_isd2 as gji
from kitqat.qroutines.linalg import gauss_jordan_isd4 as gji

# from kitqat.qroutines.linalg import gauss_jordan_isd_opt5 as gji5
from kitqat.qroutines.linalg import matrix as qmatrix
from qat.lang.AQASM.program import Program

# from numpy import argmax
from qat.core.console import display


def _prepare_circuit(r, n):
    pr = Program()
    qr_mat = pr.qalloc(r * n)
    qr_rows = qmatrix.get_rows_as_qubit_list(r, n, qr_mat)
    return pr, qr_rows


def _build_gje_circuit(r, n, n_syns, gjmod, alg="prange"):
    pr, qregs_rows = _prepare_circuit(r, n + n_syns)

    skip_rightmost = alg == "prange"
    rref_gate = gjmod.get_rref(r, n + n_syns, skip_rightmost, n)

    swap_ancillae_n, add_ancillae_n = gjmod.get_required_ancillae(r)
    swap_ancillae = pr.qalloc(swap_ancillae_n)
    if add_ancillae_n > 0:
        add_ancillae = pr.qalloc(add_ancillae_n)
        pr.apply(rref_gate, qregs_rows, swap_ancillae, add_ancillae)
    else:
        pr.apply(rref_gate, qregs_rows, swap_ancillae)

    # print(pr.qbit_count)
    return pr


def _get_max_depth_qbits(vec, qblist):
    maxd = 0
    for qb in qblist:
        curr = vec[qb]
        if curr > maxd:
            maxd = curr
    return maxd


def _compute_depth(cr, include_intermediate=False, include_gates=set()):
    vec = [0] * cr.nbqbits
    dic = {}
    # for op in pr.op_list
    for idx, op in enumerate(cr):
        if len(include_gates) > 0 and not op.gate in include_gates:
            continue
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


def _trans_qbit_to_txt(r, n, n_syns, qbits, gjmod):
    txts = []

    swap_ancillae_n, add_ancillae_n = gjmod.get_required_ancillae(r)
    # last element of matrix
    last_mat = r * (n + n_syns) - 1

    for qb in qbits:
        if qb > last_mat:
            # ancilla
            if qb > last_mat + swap_ancillae_n:
                # add_ancillae [last_mat + swap_ancillae_n: +add_ancillae_n]
                idx = qb - last_mat - swap_ancillae_n - 1
                txt = f"C[{idx}]"
            else:
                # swap_ancillae [last_mat: last_mat + swap_ancillae_n]
                idx = qb - last_mat - 1
                txt = f"B[{idx}]"
        else:
            row = qb // (n + n_syns)
            col = qb % (n + n_syns)
            if col < n:
                txt = f"L[{row},{col}(H)]"
            else:
                txt = f"L[{row},{col}(s)]"
        txts.append(txt)
    return txts


def main():
    circulant = True
    # alg = "prange"
    alg = 'lee'

    for r in range(30, 31):
        if alg == "prange":
            # with prange, we do not consider the right-most k\times n
            # submatrix, so whatever value we use the result is equal (the only
            # thing is that there are enforcements in other parts of the
            # circuit for n>r)
            k = 0
        if circulant:
            n_syns = r
            k = r
            # n = 2 * r # k = r
        else:
            k = 4 * r # mceliece, more or less
            n_syns = 1
        n = k + r

        # tmp overwrite
        n_syns = 10

        pr = _build_gje_circuit(r, n, n_syns, gji, alg)
        cr = pr.to_circ(include_matrices=False)
        # display(cr, max_depth=2)
        sts = statistics(cr)
        # print(sts)
        ccnot_n = sts["gates"].get("C-C-X", 0) + sts["gates"].get("CCNOT", 0)
        cnot_n = sts["gates"].get("C-X", 0) + sts["gates"].get("CNOT", 0)
        depth, max_depth_qubits, dic = _compute_depth(cr, include_intermediate=False)
        # depth, depth_i, dic = _compute_depth(cr, include_intermediate=False)
        trans = _trans_qbit_to_txt(r, n, n_syns, max_depth_qubits, gji)

        for op, dep in dic.items():
            print(op, dep)

        print(f"r: {r}, n: {n}, nsyns: {n_syns}, circulant: {circulant}")
        print(f"CNOT: {cnot_n}, CCNOT: {ccnot_n}")
        print(
            f"depth: {depth}, max depth qbits: {max_depth_qubits}/{cr.nbqbits},"
            f" corresponding to {trans}"
        )

        depth, max_depth_qubits, dic = _compute_depth(
            cr, include_intermediate=False, include_gates={"CCNOT"}
        )
        trans = _trans_qbit_to_txt(r, n, n_syns, max_depth_qubits, gji)
        print(
            f"CCNOT depth: {depth}, max depth qbits:"
            f" {max_depth_qubits}/{cr.nbqbits}, corresponding to {trans}"
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


if __name__ == "__main__":
    main()
