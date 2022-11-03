"""
Montgomery multiplication for polynomials
"""
from qat.lang.AQASM.gates import CCNOT, CNOT, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from qat.external.utils.qroutines import qregs_init as qregs
from collections import deque
from itertools import islice


@build_gate("M_ADD", [int], arity=lambda x: x * 2)
def madd(nbits: int) -> QRoutine:
    """Perform bitwise add |a>|b> -> |a>|a xor b>. It expects operands of the same size."""
    qf = QRoutine()
    qr1 = qf.new_wires(nbits)
    qr2 = qf.new_wires(nbits)
    for w1, w2 in zip(qr1, qr2):
        qf.apply(CNOT, w1, w2)
    return qf


@build_gate("M_CONST_ADD", [int, str], arity=lambda x, _: x)
def m_const_add(nbits: int, bitstring: str) -> QRoutine:
    """Perform bitwise add |a> -> |a xor b>, with b a constant bitstring of the same len of a."""
    qf = QRoutine()
    qr1 = qf.new_wires(nbits)
    for w1, bit in zip(qr1, bitstring):
        if bit == '1':
            qf.apply(X, w1)
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

@build_gate("M_CONST_CADD", [int, str], arity=lambda x, _: x  + 1)
def m_const_cadd(nbits: int, bitstring: str) -> QRoutine:
    """Controlled bitwise add |ctrl>|a> -> |ctrl>|a xor b>, with b constant bitstring of the same len of a."""
    qf = QRoutine()
    ctrl = qf.new_wires(1)
    qr1 = qf.new_wires(nbits)
    for w1, bit in zip(qr1, bitstring):
        if bit == '1':
            qf.apply(CNOT, ctrl, w1)
    return qf


@build_gate("M_MUL", [int], arity=lambda x: x * 5 + 4)
def mmul1(k: int) -> QRoutine:
    """It performs |a>|b>|0...0>|n>|anc> -> |a>|b>|a*b*r^{-1}>|n>|anc>.
    Sizes should be |k+1>|k+1>|k+1>|k+1>|k>.

    Note that a and b, being inside the field GF(2)[X], should be of length k.
    However, we expect them to be of length k-1 in order to perform the sums. The bit in position 0 is expected to be in state |0>.
    n, on the other hand, is the reduction polynomial, of rank k and therefore outside of GF(2)[x]. It's size is already k+1.

    As for the classic version (see my
    https://github.com/crypto-stuff/algebraic repo), the bit in position 0 is
    the MSB, the one in position k-1 is the LSB.
    """
    qf = QRoutine()
    ar = qf.new_wires(k + 1)
    br = qf.new_wires(k + 1)
    cr = qf.new_wires(k + 1)
    nr = qf.new_wires(k + 1)
    anc = qf.new_wires(k)

    c_dq = deque([qb for qb in cr])
    adder = mcadd(k + 1)
    for i, abit in enumerate(reversed(ar[1:])):
        qf.apply(adder, abit, br, c_dq)
        qf.apply(CNOT, c_dq[k], anc[i])
        qf.apply(adder, anc[i], nr, c_dq)
        c_dq.rotate()
    return qf

@build_gate("M_MUL", [int], arity=lambda x: x * 5)
def mmul2(k: int) -> QRoutine:
    """It performs |a>|b>|0...0>|n>|anc> -> |a>|b>|a*b*r^{-1}>|n>|anc>.
    Sizes should be |k>|k>|k>|k>|k>.

    Note that a and b, being inside the field GF(2)[X], should be of length k.
    n, on the other hand, is the reduction polynomial, of rank k and therefore
    outside of GF(2)[x]. It's size is k+1. However, being of rank k, the bit in
    position 0 (corresponding to x^k) is always 1.

    As for the classic version (see my
    https://github.com/crypto-stuff/algebraic repo), the bit in position 0 is
    the MSB, the one in position k-1 is the LSB.

    """
    qf = QRoutine()
    ar = qf.new_wires(k)
    br = qf.new_wires(k)
    cr = qf.new_wires(k)
    nr = qf.new_wires(k)
    ancr = qf.new_wires(k)

    c_dq = deque([qb for qb in cr])
    adder = mcadd(k)
    for i, abit in enumerate(reversed(ar)):
        qf.apply(adder, abit, br, c_dq)
        qf.apply(CNOT, c_dq[k-1], ancr[i])
        qf.apply(adder, ancr[i], nr, c_dq)
        c_dq.rotate()
        qf.apply(CNOT, ancr[i], c_dq[0])
    return qf


@build_gate("M_MUL", [int], arity=lambda x: x * 4 - 1)
def mmul3(k: int) -> QRoutine:
    """TODO Version from Jang et al. 2021 of func:`qat.external.utils.qroutines.montgomery.arith.mmul2`.
    Without ancillae.

    It performs |a>|b>|0...0> -> |a>|b>|a*b*r^{-1}>|anc> using a fixed
    modulus n. Even if n is a bitstring of length k+1, we already know that
    n[k] (the MSB, = x^k) is 1. For this reason, we expect the n qreg to be of
    length k.

    Length of registers are |k>|k>|k>|k>.

    Check :

    """
    qf = QRoutine()
    ar = qf.new_wires(k)
    br = qf.new_wires(k)
    cr = qf.new_wires(k)
    # Since we do not take LSB and MSB of n as input
    nr = qf.new_wires(k-1)

    c_dq = deque([qb for qb in cr])
    cadder1 = mcadd(k)
    # we skip the LSB of modulus. We know it's 1 already.
    cadder2 = mcadd(k-1)
    for i, abit in enumerate(reversed(ar)):
        qf.apply(cadder1, abit, br, c_dq)
        qf.apply(cadder2, c_dq[k-1], nr, list(islice(c_dq, 0, k-1)))
        c_dq.rotate()
    return qf


@build_gate("M_MUL_FIXED_N", [int, str], arity=lambda x, _: x * 4 + 3)
def mmul_fixed_n(k: int, modulus: str) -> QRoutine:
    """It performs |a>|b>|0...0>|anc> -> |a>|b>|a*b*r^{-1}>|anc> using a fixed
    modulus n, expected to be a bitstring of length k+1. Sizes should be
    |k+1>|k+1>|k+1>|k>.

    Check :func:`qat.external.utils.qroutines.montgomery.arith.mmul`


    """
    qf = QRoutine()
    ar = qf.new_wires(k + 1)
    br = qf.new_wires(k + 1)
    cr = qf.new_wires(k + 1)
    anc = qf.new_wires(k)

    c_dq = deque([qb for qb in cr])
    # c idxs are [2k + 1, ..., 3k]
    adder = mcadd(k + 1)
    const_cadder = m_const_cadd(k, modulus)
    for i, abit in enumerate(reversed(ar[1:])):
        # b,c -> b,b+c; conditioned on abit=1
        qf.apply(adder, abit, br, c_dq)
        #
        qf.apply(CNOT, c_dq[k], anc[i])
        qf.apply(const_cadder, anc[i], c_dq)
        #
        # qf.apply(CNOT, c_dq[k], anc[i])
        qf.apply(const_cadder, c_dq[k], list(c_dq)[:k])
        c_dq.rotate()
    return qf

@build_gate("M_MUL_FIXED_N", [int, str], arity=lambda x, _: x * 4)
def mmul_fixed_n2(k: int, modulus: str) -> QRoutine:
    """Optimized version of func:`qat.external.utils.qroutines.montgomery.arith.mmul2`.
    It performs |a>|b>|0...0>|anc> -> |a>|b>|a*b*r^{-1}>|anc> using a fixed
    modulus n. Even if n is a bitstring of length k+1, we already know that
    n[k] (the MSB, = x^k) is 1. For this reason, we expect the n qreg to be of
    length k.

    Length of registers are |k>|k>|k>|k>.

    Check :

    """
    qf = QRoutine()
    ar = qf.new_wires(k)
    br = qf.new_wires(k)
    cr = qf.new_wires(k)
    ancr = qf.new_wires(k)

    c_dq = deque([qb for qb in cr])
    adder = mcadd(k)
    const_cadder = m_const_cadd(k, modulus)
    for i, abit in enumerate(reversed(ar)):
        qf.apply(adder, abit, br, c_dq)
        qf.apply(CNOT, c_dq[k-1], ancr[i])
        # qf.apply(adder, ancr[i], nr, c_dq)
        qf.apply(const_cadder, ancr[i], c_dq)
        c_dq.rotate()
        qf.apply(CNOT, ancr[i], c_dq[0])
    return qf


@build_gate("M_MUL_FIXED_N", [str], arity=lambda x: (len(x)+1) * 3)
def mmul_fixed_n3(modulus: str) -> QRoutine:
    """TODO Version from Jang et al. 2021 of func:`qat.external.utils.qroutines.montgomery.arith.mmul2`.
    It performs |a>|b>|0...0>|anc> -> |a>|b>|a*b*r^{-1}>|anc> using a fixed
    modulus n. Even if n is a bitstring of length k+1, we already know that
    n[k] (the MSB, = x^k) is 1; same for n[0]. For this reason, we expect the n qreg to be of
    length k-1, i.e. modulus = n[1:k]

    Length of registers are |k>|k>|k>|k>.

    Check :

    """
    qf = QRoutine()
    k = len(modulus) + 1
    ar = qf.new_wires(k)
    br = qf.new_wires(k)
    cr = qf.new_wires(k)

    c_dq = deque([qb for qb in cr])
    adder = mcadd(k)
    # we skip the MSB and LSB of modulus. We know it's 1 already.
    const_cadder = m_const_cadd(k-1, modulus)
    for i, abit in enumerate(reversed(ar)):
        qf.apply(adder, abit, br, c_dq)
        qf.apply(const_cadder, c_dq[k-1], list(islice(c_dq, 0, k-1)))
        c_dq.rotate()
    return qf

# @build_gate("M_EXP_FIXED_N_FIXED_E", [int, str, str])
# # def mexp(a: bitarray, e: bitarray, n: bitarray, r: bitarray) -> bitarray:
# def mexp_fixed_n(k: int, modulus: str, exp: str, r: str) -> QRoutine:
#     """e is the exponent, in binary form, \nin the field.
#     c is first initialized to the Montgomery multiplicative unit, i.e. r
#     """
#     qf = QRoutine()
#     ar = qf.new_wires(k + 1)
#     cr = qf.new_wires(k + 1)
#     # TODO get exact dimension
#     ancr = qf.new_wires(k * 2)
#     qf.apply(qregs.initialize_qureg_given_bitstring(r, False), cr)

#     # first bit (MSB) of exponent shoud be 1
#     exp_start = e.find(1)
#     if exp_start < 0:
#         return qf

#     cmul = mmul_fixed_n(k, modulus)
#     for ebit in reversed(exp[exp_start:]):
#         if ebit:
#             cmul(cr, ar, )
#             c = mul_simple3(c, an, n)
#         an = square_simple1(an, n)
#     return c
