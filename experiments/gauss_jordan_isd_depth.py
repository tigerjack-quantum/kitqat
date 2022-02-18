# from qat.external.utils.qroutines.fake import fake_gate
from qat.external.utils.qroutines.linalg import gauss_jordan_isd as gji
from qat.external.utils.qroutines.linalg import matrix as qmatrix
from qat.lang.AQASM.program import Program


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
    # add_name_to_qbits_following_pattern(pr, {
    #     'cadd': add_ancillae,
    #     'swap': swap_ancillae
    # })
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

def _compute_depth(pr):
    vec = [0] * pr.qbit_count
    cr = pr.to_circ()
    # for op in pr.op_list:
    for op in cr:
        print(op)
        print(vec)
        maxd = _get_max_depth_qbits(vec, op.qbits)
        print(maxd)
        for qb in op.qbits:
            vec[qb] = maxd + 1
    return max(vec)



def main():
    pr = _build_gje_circuit(3, 4)
    print(_compute_depth(pr))



if __name__ == '__main__':
    main()
