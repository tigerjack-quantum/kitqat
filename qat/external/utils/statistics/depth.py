def _get_max_depth_qbits(vec, qblist):
    maxd = 0
    for qb in qblist:
        curr = vec[qb]
        if curr > maxd:
            maxd = curr
    return maxd


def compute_circuit_depth(cr, include_intermediate=False):
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
