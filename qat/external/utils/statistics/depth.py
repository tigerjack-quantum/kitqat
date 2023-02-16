def _get_max_depth_qbits(vec, qblist):
    maxd = 0
    for qb in qblist:
        curr = vec[qb]
        if curr > maxd:
            maxd = curr
    return maxd


def compute_circuit_depth(cr, include_intermediate=False) -> tuple[int, list[int], dict[str, int]]:
    """ Compute depth of the circuit using dynamic programming.

    :param cr: qat Circuit object
    :param include_intermediate: boolean value, set to True to also include the intermediate depth

    :return the maximum depth;
            the list of qubits having that depth;
            a dictionary of intermediate results, whose keys are strings containing indexes, the gate name and the qubits positions and whose values is the (intermediate) depth after the operation
    """
    vec = [0] * cr.nbqbits
    dic = {}
    # for op in pr.op_list
    for idx, op in enumerate(cr):
        maxd = _get_max_depth_qbits(vec, op.qbits)
        for qb in op.qbits:
            vec[qb] = maxd + 1
        if include_intermediate:
            dic[f"{idx}_{op.gate}_{op.qbits}"] = maxd + 1
        #     print(vec)
    m = max(vec)
    argmaxs = [i for i, j in enumerate(vec) if j == m]
    return m, argmaxs, dic
