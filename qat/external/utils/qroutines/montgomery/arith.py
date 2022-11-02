"""
Multiple precision Montgomery multiplication 
"""
from qat.lang.AQASM.gates import CCNOT, CNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from collections import deque


@build_gate("M_ADD", [int], arity=lambda x: x * 2)
def madd(nbits: int) -> QRoutine:
    """Perform bitwise add |a>|b> -> |a>|a xor b>. It expects operands of the same size."""
    qf = QRoutine()
    qr1 = qf.new_wires(nbits)
    qr2 = qf.new_wires(nbits)
    for w1, w2 in zip(qr1, qr2):
        qf.apply(CNOT, w1, w2)
    return qf


@build_gate("M_CADD", [int], arity=lambda x: x * 2 + 1)
def mcadd(nbits: int) -> QRoutine:
    """Controlled bitwise add |ctrl>|a>|b> -> |ctrl>|a>|a xor b>. It expects
    operands of the same size."""
    qf = QRoutine()
    ctrl = qf.new_wires(1)
    qr1 = qf.new_wires(nbits)
    qr2 = qf.new_wires(nbits)
    for w1, w2 in zip(qr1, qr2):
        qf.apply(CCNOT, ctrl, w1, w2)
    return qf


@build_gate("M_MUL", [int], arity=lambda x: x * 5 + 5)
def mmul(k: int) -> QRoutine:
    """It performs |a>|b>|0...0>|n>|anc> -> |a>|b>|a*b*r^{-1}>|n>|anc>.
    Sizes should be |k>|k>|k>|k+1>|k>.

    Note that, while a and b are of the same size, n is 1 qubit bigger. Indeed
    n is the reduction polynomial, of rank k and therefore outside of GF(2)[x],
    while a and b are inside the field, and therefore or rank at most k-1.

    As for the classic version (see my
    https://github.com/crypto-stuff/algebraic repo), the bit in position 0 is
    the MSB, the one in position k-1 is the LSB.

    Version 2 (par. 4) of [1] a(x) b(x) x^{-k} mod n(x)
    """
    qf = QRoutine()
    ar = qf.new_wires(k + 1)
    # qf.set_ancillae(a[0])
    br = qf.new_wires(k + 1)
    # qf.set_ancillae(b[0])
    cr = qf.new_wires(k + 1)
    # qf.set_ancillae(c[0])
    nr = qf.new_wires(k + 1)
    anc = qf.new_wires(k + 1)

    c_dq = deque([qb for qb in cr])
    # c idxs are [2k + 1, ..., 3k]
    adder = mcadd(k + 1)
    print(adder.arity)
    for i, abit in enumerate(reversed(ar[1:])):
        qf.apply(adder, abit, br, c_dq)
        qf.apply(CNOT, c_dq[k], anc[i])
        qf.apply(adder, anc[i], nr, c_dq)
        c_dq.rotate()
    return qf
