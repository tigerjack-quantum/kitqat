"""Note that the add_const and add_mod requires a proper implementation of their gates

Implementations were taken from.

[1]
[2] Lecture notes not_04 from Crypto course
[3]
"""
from collections import deque

from qat.external.qroutines.arith import cuccaro_arith as cuccadd
from qat.lang.AQASM.arithmetic import add_const, add_mod
from qat.lang.AQASM.gates import CNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine


@build_gate("M_MUL_CONSTMOD", [str], arity=lambda x: len(x) * 4 + 1)
def mul_mod(nbitstr: str) -> QRoutine:
    """It perfoms |a>|b>|0> -> |a>|b>|a*b mod(n)> in Montgomery domain.

    :param nbitstr: is the bitstring (in LITTLE ENDIAN format, i.e. element at index 0 is the LSB)
    of length d.

    The multiplication is therefore between two qreg of length d, mod
    int(nbitstr).

    Alg. 6.2 of [2] w/out the useless extension on A_d and without the final check on x >= n
    """
    d = len(nbitstr)
    nn = int(nbitstr[::-1], 2)
    qf = QRoutine()
    areg = qf.new_wires(d)
    # qf.set_ancillae(areg[d])
    breg = qf.new_wires(d)
    # + 1 for the overflow qbit
    creg = qf.new_wires(d + 1)
    qf.set_ancillae(creg[d])
    anc_reg = qf.new_wires(d)
    c_dq = deque([qb for qb in creg])
    # print(f"no rotate {[qb.index for qb in c_dq]}")
    c_dq.rotate(-1)
    # print(f"rotate {[qb.index for qb in c_dq]}")

    # ninv = 1
    qadd = cuccadd.adder.circuit_generator(
        d, d, overflow_qbit=True, little_endian=True
    )
    qaddc = qadd.ctrl(1)
    qaddconstc = add_const(len(creg), nn).ctrl()

    qf.apply(qaddc, areg[0], breg, c_dq)
    # for i in range(1, d):
    for i in range(1, d):
        # print("-" * 5, i, "-" * 5)
        # if x[0] -> x += N
        # right-shift x
        # if A[i] -> x+=B
        # print(f"Applied CNOT(c[0], anc[{i}])")
        qf.apply(CNOT, c_dq[0], anc_reg[i])
        # print(f"If anc[{i}] -> add(c, N)")
        qf.apply(qaddconstc, anc_reg[i], c_dq)
        c_dq.rotate(-1)
        # print(f"rotate {[qb.index for qb in c_dq]}")
        # print(f"C-ADD (a[{i}], b, c)")
        qf.apply(qaddc, areg[i], breg, c_dq)
    # print("-" * 5, "last", "-" * 5)
    qf.apply(CNOT, c_dq[0], anc_reg[-1])
    qf.apply(qaddconstc, anc_reg[-1], c_dq)
    c_dq.rotate(-1)
    # print(f"rotate {[qb.index for qb in c_dq]}")
    return qf

