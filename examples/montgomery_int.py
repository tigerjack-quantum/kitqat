import numpy as np
from qat.core.console import display
from qat.external.qpus import reversible
from qat.external.utils.bits.conversion import get_bitstring_from_int
from qat.external.utils.qroutines.algebraic.gfp import montgomery_arith as marith
from qat.external.utils.qroutines.qregs_init import initialize_qureg_given_bitarray, initialize_qureg_given_int
from qat.external.utils.statistics.depth import compute_circuit_depth
from qat.lang.AQASM.program import Program
from qat.external.qpus.reversible import RProgram
from qat.lang.AQASM.arithmetic import add_mod
from qat.lang.AQASM import classarith, qftarith
from qat.external.utils.qatmgmt import statistics as estats


def euclidean_alg_int(a: int, b: int):
    u = np.array([a, 1, 0])
    v = np.array([b, 0, 1])
    w = np.array([None] * 3)
    # print(f"u = {u}, v = {v}")

    while (w[0] != 0):
        q = int(np.floor(u[0] / v[0]))
        w = u - q * v
        u = v
        v = w
        # print(f"q = {q}, w = {w}, u = {u}, v = {v}")

    d = u[0]
    e = u[1]
    f = u[2]

    return (d, e, f)


def mod_red():
    a, b, n = 4, 8, 11
    d = 4
    r = 2**d
    # r^{-1} = 9
    nbitstr = bin(n)[2:].zfill(d)
    # These are the results after conversion: mu(a) = 9; mu(b) = 7;
    # mul(mu(a) * mu(b)) = mu(a) * mu(b) * r^{-1} = 6
    ress_exp = {'a': 9, 'b': 7, 'add': 5, 'mul': 6}

    qbit_names = {
        'a': range(0, d),
        'b': range(d, 2 * d),
        'anc': range(2 * d, 2 * d + 1)
    }

    progA = Program()
    areg = progA.qalloc(d)
    breg = progA.qalloc(d)

    progA.apply(initialize_qureg_given_int(ress_exp['a'], d, True), areg)
    progA.apply(initialize_qureg_given_int(ress_exp['b'], d, True), breg)
    progA.apply(add_mod(d, n), areg, breg)

    circ = progA.to_circ(include_matrices=False,
                         submatrices_only=True,
                         link=[qftarith])
    rcr = RProgram.circuit_to_rprogram(circ, qbit_names)
    res = rcr.get_result_by_name()
    print(res)
    stats = circ.statistics()
    print(stats)
    print(estats.reformat_statistics(stats))
    print(compute_circuit_depth(circ))

    pass


def main():
    mod_red()


if __name__ == '__main__':
    main()
