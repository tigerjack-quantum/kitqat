from collections import deque
from copy import deepcopy

import numpy as np
from qat.external.qpus.reversible import RProgram
from qat.external.utils.qatmgmt import statistics as estats
from qat.external.qroutines import adder as cuccadd
from qat.external.qroutines.algebraic.gfp import montgomery_arith as marith
from qat.external.qroutines.qregs_init import initialize_qureg_given_int
from qat.external.utils.statistics.depth import compute_circuit_depth
from qat.lang.AQASM import classarith
from qat.lang.AQASM.arithmetic import add_mod
from qat.lang.AQASM.classarith import add_const
from qat.lang.AQASM.gates import CNOT
from qat.lang.AQASM.program import Program


def euclidean_alg_int(a: int, b: int):
    u = np.array([a, 1, 0])
    v = np.array([b, 0, 1])
    w = np.array([None] * 3)
    # print(f"u = {u}, v = {v}")

    while w[0] != 0:
        q = int(np.floor(u[0] / v[0]))
        w = u - q * v
        u = v
        v = w
        # print(f"q = {q}, w = {w}, u = {u}, v = {v}")

    d = u[0]
    e = u[1]
    f = u[2]

    return (d, e, f)


def _debug_circ_status(prog, qbit_names):
    circ = prog.to_circ(
        include_matrices=False, submatrices_only=True, link=[classarith]
    )
    rcr = RProgram.circuit_to_rprogram(circ, qbit_names)
    ress = rcr.get_result_by_name()
    print(ress)
    return circ, rcr, ress


def _analyze_and_print(prog, qbit_names, qbit_res_name, res_exp):
    circ, _, ress = _debug_circ_status(prog, qbit_names)
    res = ress[qbit_res_name].to01()[::-1]
    print(res)
    assert int(res, 2) == res_exp, f"Expected {res_exp}, got {int(res, 2)}"
    stats = circ.statistics()
    # print(stats)
    print(estats.reformat_statistics(stats))
    print(compute_circuit_depth(circ))


def _mod_red_common(nn: int, d: int, ress_exp: dict, inline: bool):
    nbitstr = bin(nn)[2:].zfill(d)[::-1]

    prog = Program()
    areg = prog.qalloc(d)
    breg = prog.qalloc(d)
    prog.apply(initialize_qureg_given_int(ress_exp["a"], d, True), areg)
    prog.apply(initialize_qureg_given_int(ress_exp["b"], d, True), breg)
    qbit_names = {
        "a": range(0, d),
        "b": range(d, 2 * d),
    }

    print("*" * 20)
    print("ADD MOD")
    progA = deepcopy(prog)
    progA.apply(add_mod(d, nn), areg, breg)
    _analyze_and_print(progA, qbit_names, "b", ress_exp["add"])

    print("*" * 20)
    print("MUL MOD")
    progB = deepcopy(prog)
    creg = progB.qalloc(d)
    anc_reg = progB.qalloc(d)
    qbit_names["c"] = range(2 * d, 3 * d)
    qbit_names["anc"] = range(3 * d, 4 * d)
    _debug_circ_status(progB, qbit_names)
    if not inline:
        qfun = marith.mul_mod.circuit_generator(nbitstr)
        progB.apply(qfun, areg, breg, creg, anc_reg)
    else:
        # INLINE

        anc_areg = progB.qalloc(1)
        qbit_names["a_ext"] = range(16, 17)
        areg_ext = [qb for qb in areg] + [anc_areg[0]]
        # + 1 for the overflow qbit
        anc_creg = progB.qalloc(1)
        qbit_names["c_ext"] = range(17, 18)
        creg_ext = [qb for qb in creg] + [anc_creg[0]]
        cext_dq = deque([qb for qb in creg_ext])

        # npr_0 is always 1
        qadd = cuccadd.adder.circuit_generator(
            d, d, overflow_qbit=True, little_endian=True
        )
        # 1st iteration is only this add
        #
        # This is useless, but it will help to obtain the registers in the same
        # order at the end of the circuit
        cext_dq.rotate(-1)
        progB.apply(qadd.ctrl(1), areg_ext[0], breg, cext_dq)
        _, rcr, _ = _debug_circ_status(progB, qbit_names)
        # display(circ)
        print(f"rotate {[qb.index for qb in cext_dq]}")
        print([rcr.rbits[qb.index] for qb in cext_dq])

        for i in range(1, d):
            print("-" * 5, i, "-" * 5)
            # if c[0] -> c += N
            # right-shift c
            # if A[i] -> c+=B
            print(f"Applied CNOT(c[0], anc[{i}])")
            progB.apply(CNOT, cext_dq[0], anc_reg[i])
            print(f"If anc[{i}] -> add(c, N)")
            progB.apply(add_const(len(creg_ext), nn).ctrl(), anc_reg[i], cext_dq)
            _, rcr, _ = _debug_circ_status(progB, qbit_names)
            print([rcr.rbits[qb.index] for qb in cext_dq])

            cext_dq.rotate(-1)
            print(f"rotate {[qb.index for qb in cext_dq]}")
            print([rcr.rbits[qb.index] for qb in cext_dq])

            print(f"C-ADD (a[{i}], b, c)")
            progB.apply(qadd.ctrl(), areg_ext[i], breg, cext_dq)
            _, rcr, _ = _debug_circ_status(progB, qbit_names)
            print([rcr.rbits[qb.index] for qb in cext_dq])

        # last iteration
        print("-" * 5, "last", "-" * 5)
        progB.apply(CNOT, cext_dq[0], anc_reg[-1])
        progB.apply(add_const(len(creg_ext), nn).ctrl(), anc_reg[-1], cext_dq)
        _, rcr, _ = _debug_circ_status(progB, qbit_names)
        cext_dq.rotate(-1)
        print(f"rotate {[qb.index for qb in cext_dq]}")
        print([rcr.rbits[qb.index] for qb in cext_dq])
        # END INLINE

    _analyze_and_print(progB, qbit_names, "c", ress_exp["mul"])


def mod_red1():
    d = 4
    # a, b = 4, 8
    # r = 2**d
    nn = 11
    # r^{-1} = 9
    # reversed since we'll work in little endian
    # These are the results after conversion: mu(a) = 9; mu(b) = 7;
    # mul(mu(a) * mu(b)) = mu(a) * mu(b) * r^{-1} = 6
    ress_exp = {"a": 9, "b": 7, "add": 5, "mul": 6}
    _mod_red_common(nn, d, ress_exp, False)


def mod_red2():
    d = 5
    # a, b = 4, 8
    # r = 2**d
    nn = 29
    # These are the results after conversion: a = mu(a); b = mu(b);
    # mul(mu(a) * mu(b)) = mu(a) * mu(b) * r^{-1} = 6
    ress_exp = {"a": 10, "b": 22, "add": 3, "mul": 25}
    _mod_red_common(nn, d, ress_exp, False)


def main():
    mod_red1()
    mod_red2()


if __name__ == "__main__":
    main()
