__author__ = "Federico Pinto <federico.pinto@mail.polimi.it>"
# Author: Federico Pinto
import numpy as np
from qat.lang.AQASM.gates import CNOT, CCNOT, SWAP, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from qatext.qroutines.arith.cuccaro_arith import adder as cuccaro_adder

# --- GF(2) Linear Algebra Helpers for Karatsuba ---

def gf2_lup(matrix):
    """
    Computes the LUP decomposition of a square matrix over GF(2).
    Returns L, U, P such that P @ matrix = L @ U.
    """
    n = len(matrix)
    L = np.eye(n, dtype=int)
    U = matrix.copy().astype(int)
    P = np.eye(n, dtype=int)
    for i in range(n):
        pivot = -1
        for j in range(i, n):
            if U[j, i] == 1:
                pivot = j
                break
        if pivot == -1:
            continue
        if pivot != i:
            U[[i, pivot]] = U[[pivot, i]]
            P[[i, pivot]] = P[[pivot, i]]
            L[[i, pivot], :i] = L[[pivot, i], :i]
        for j in range(i + 1, n):
            if U[j, i] == 1:
                U[j] = (U[j] + U[i]) % 2
                L[j, i] = 1
    return L, U, P


def get_mod_matrix(n, m_bits, c_bits):
    """
    Generates the n x n matrix representing multiplication by a constant C(x) mod m(x).
    m_bits and c_bits are integers representing polynomial coefficients.
    """
    matrix = np.zeros((n, n), dtype=int)
    for j in range(n):
        val = c_bits << j
        for d in range(n + j, n - 1, -1):
            if (val >> d) & 1:
                val ^= (m_bits << (d - n))
        for i in range(n):
            matrix[i, j] = (val >> i) & 1
    return matrix


# --- Sub-blocks for the Karatsuba Multiplier ---

@build_gate("MODSHIFT", [int, int], arity=lambda n, m: n)
def modshift_gate(n, m_bits):
    """ Reversible Modular Shift H <- x * H mod m(x)."""
    qrout = QRoutine()
    reg = qrout.new_wires(n)
    for i in range(n - 1, 0, -1):
        qrout.apply(SWAP, reg[i], reg[i-1])
    for d in range(1, n):
        if (m_bits >> d) & 1:
            qrout.apply(CNOT, reg[0], reg[d])
    return qrout


@build_gate("CONSTMODMULT", [int, int, int], arity=lambda n, m, c: n)
def constmodmult_gate(n, m_bits, c_bits):
    """In-place modular multiplication by a constant polynomial C(x)."""
    matrix = get_mod_matrix(n, m_bits, c_bits)
    L, U, P = gf2_lup(matrix)
    qrout = QRoutine()
    reg = qrout.new_wires(n)
    for i in range(n):
        for j in range(i + 1, n):
            if U[i, j]:
                qrout.apply(CNOT, reg[j], reg[i])
    for i in range(n - 1, -1, -1):
        for j in range(i):
            if L[i, j]:
                qrout.apply(CNOT, reg[j], reg[i])
    p_inv_indices = [np.where(col == 1)[0][0] for col in P.T]
    curr = list(range(n))
    for i in range(n):
        target = p_inv_indices[i]
        if curr[i] != target:
            loc = curr.index(target)
            qrout.apply(SWAP, reg[i], reg[loc])
            curr[i], curr[loc] = curr[loc], curr[i]
    return qrout


@build_gate("KMULT1xK", [int, int], arity=lambda n, k: 2*n + (2*n + k - 1))
def kmult1xk_gate(n, k):
    """Reversible multiplier for (1 + x^k) * f(x) * g(x)."""
    qrout = QRoutine()
    reg_f, reg_g = qrout.new_wires(n), qrout.new_wires(n)
    reg_h = qrout.new_wires(2*n + k - 1)
    l = max(0, 2*n - 1 - k)
    if n > 1:
        for i in range(l):
            if 2*k + i < 2*n + k - 1:
                qrout.apply(CNOT, reg_h[2*k + i], reg_h[k + i])
        for i in range(k):
            if k + i < 2*n + k - 1:
                qrout.apply(CNOT, reg_h[k + i], reg_h[i])
        qrout.apply(kmult_gate(n), reg_f, reg_g, reg_h[k : k + 2*n - 1])
        for i in range(k):
            if k + i < 2*n + k - 1:
                qrout.apply(CNOT, reg_h[k + i], reg_h[i])
        for i in range(l):
            if 2*k + i < 2*n + k - 1:
                qrout.apply(CNOT, reg_h[2*k + i], reg_h[k + i])
    else:
        qrout.apply(CCNOT, reg_f[0], reg_g[0], reg_h[0])
        qrout.apply(CCNOT, reg_f[0], reg_g[0], reg_h[k])
    return qrout


@build_gate("KMULT", [int], arity=lambda n: 2*n + (2*n - 1))
def kmult_gate(n):
    """Reversible Non-Modular Karatsuba Multiplier."""
    qrout = QRoutine()
    reg_f, reg_g = qrout.new_wires(n), qrout.new_wires(n)
    reg_h = qrout.new_wires(2*n - 1)
    if n == 1:
        qrout.apply(CCNOT, reg_f[0], reg_g[0], reg_h[0])
        return qrout
    k = n // 2
    nk = n - k
    qrout.apply(kmult1xk_gate(k, k), reg_f[0:k], reg_g[0:k], reg_h[0 : 3*k - 1])
    qrout.apply(kmult1xk_gate(nk, k), reg_f[k:n], reg_g[k:n], reg_h[k : k + 2*nk + k - 1])
    for i in range(k):
        qrout.apply(CNOT, reg_f[i], reg_f[k+i])
        qrout.apply(CNOT, reg_g[i], reg_g[k+i])
    qrout.apply(kmult_gate(nk), reg_f[k:n], reg_g[k:n], reg_h[k : k + 2*nk - 1])
    for i in range(k):
        qrout.apply(CNOT, reg_f[i], reg_f[k+i])
        qrout.apply(CNOT, reg_g[i], reg_g[k+i])
    return qrout


@build_gate("KARATSUBA", [int, int], arity=lambda n, m: 3*n)
def karatsuba_modular(n, m_bits):
    """Improved Modular Karatsuba Multiplier."""
    qrout = QRoutine()
    reg_f, reg_g, reg_h = qrout.new_wires(n), qrout.new_wires(n), qrout.new_wires(n)
    k = (n + 1) // 2
    nk = n - k
    qrout.apply(kmult_gate(k), reg_f[0:k], reg_g[0:k], reg_h[0 : 2*k - 1])
    modshift = modshift_gate(n, m_bits)
    for _ in range(k):
        qrout.apply(modshift.dag(), reg_h)
    qrout.apply(kmult_gate(nk), reg_f[k:n], reg_g[k:n], reg_h[0 : 2*nk - 1])
    c_bits = 1 | (1 << k)
    qrout.apply(constmodmult_gate(n, m_bits, c_bits), reg_h)
    for i in range(nk):
        qrout.apply(CNOT, reg_f[k+i], reg_f[i])
        qrout.apply(CNOT, reg_g[k+i], reg_g[i])
    qrout.apply(kmult_gate(k), reg_f[0:k], reg_g[0:k], reg_h[0 : 2*k - 1])
    for i in range(nk):
        qrout.apply(CNOT, reg_f[k+i], reg_f[i])
        qrout.apply(CNOT, reg_g[k+i], reg_g[i])
    for _ in range(k):
        qrout.apply(modshift, reg_h)
    return qrout

# --- TOOM-COOK 3 ---

# --- Reversible Arithmetic Primitives ---

def copy_qreg(qrout, src, dest, offset_src=0, offset_dest=0, length=None):
    """copy helper"""
    if length is None:
        length = len(src) - offset_src
    for i in range(length):
        qrout.apply(CNOT, src[offset_src + i], dest[offset_dest + i])

def toom_add_n(n: int) -> QRoutine:
    """ripple-carry adder: |a>|b>|cin> -> |a>|a+b>|cin>."""
    qrout = QRoutine()
    a, b = qrout.new_wires(n), qrout.new_wires(n)
    cin = qrout.new_wires(1)
    qrout.set_ancillae(cin)
    qrout.apply(cuccaro_adder(n, n, False, False), a, b, cin)
    return qrout

def toom_sub_n(n: int) -> QRoutine:
    """ripple-carry subtractor: |a>|b>|cin> -> |a>|b-a>|cin>."""
    qrout = QRoutine()
    a, b = qrout.new_wires(n), qrout.new_wires(n)
    cin = qrout.new_wires(1)
    qrout.set_ancillae(cin)
    qrout.apply(cuccaro_adder(n, n, False, False).dag(), a, b, cin)
    return qrout

@build_gate("TOOM_MULT_PRIM", [int, int, bool, bool])
def toom_mult_prim(size_a, size_b, signed_a=False, signed_b=False):
    """multiplier with sign extension support."""
    qrout = QRoutine()
    a, b = qrout.new_wires(size_a), qrout.new_wires(size_b)
    res = qrout.new_wires(size_a + size_b)
    for i in range(size_a - 1, -1, -1):
        target_size = size_b + i + 1
        ext_b = qrout.new_wires(target_size)
        qrout.set_ancillae(ext_b)
        copy_qreg(qrout, b, ext_b, offset_dest=(i + 1))
        if signed_b:
            for k in range(i + 1):
                qrout.apply(CNOT, b[0], ext_b[k])
        is_sub = (i == 0 and signed_a)
        gate = toom_sub_n(target_size) if is_sub else toom_add_n(target_size)
        qrout.apply(gate.ctrl(), a[i], ext_b, res[0:target_size])
        if signed_b:
            for k in range(i + 1):
                qrout.apply(CNOT, b[0], ext_b[k])
        copy_qreg(qrout, b, ext_b, offset_dest=(i + 1)) # uncompute
    return qrout

# --- Main Toom-Cook 3 Logic ---

@build_gate("TOOM3_EVAL", [int])
def toom3_eval(n: int) -> QRoutine:
    """Evaluation block: computes x(0), x(inf), x(1), x(-1), x(-2)."""
    qrout = QRoutine()
    j = n // 3
    x = qrout.new_wires(n)
    res_0, res_inf, res_1, res_m1, res_m2 = [
        qrout.new_wires(k) for k in [j, j, j + 2, j + 2, j + 3]
    ]
    x2, x1, x0 = x[0:j], x[j:2*j], x[2*j:n]

    copy_qreg(qrout, x0, res_0)
    copy_qreg(qrout, x2, res_inf)

    # temp_a = x0 + x2
    temp_a = qrout.new_wires(j + 1)
    qrout.set_ancillae(temp_a)
    copy_qreg(qrout, x0, temp_a, offset_dest=1)
    ext_x2 = qrout.new_wires(j + 1)
    qrout.set_ancillae(ext_x2)
    copy_qreg(qrout, x2, ext_x2, offset_dest=1)
    qrout.apply(toom_add_n(j+1), ext_x2, temp_a)
    copy_qreg(qrout, x2, ext_x2, offset_dest=1)

    # res_1 e res_m1
    copy_qreg(qrout, temp_a, res_1, offset_dest=1)
    copy_qreg(qrout, temp_a, res_m1, offset_dest=1)
    ext_x1 = qrout.new_wires(j+2)
    qrout.set_ancillae(ext_x1)
    copy_qreg(qrout, x1, ext_x1, offset_dest=2)
    qrout.apply(toom_add_n(j+2), ext_x1, res_1)
    qrout.apply(toom_sub_n(j+2), ext_x1, res_m1)
    copy_qreg(qrout, x1, ext_x1, offset_dest=2)

    # temp_b
    temp_b = qrout.new_wires(j + 2)
    qrout.set_ancillae(temp_b)
    copy_qreg(qrout, res_m1, temp_b)
    ext_x2_b = qrout.new_wires(j+2)
    qrout.set_ancillae(ext_x2_b)
    copy_qreg(qrout, x2, ext_x2_b, offset_dest=2)
    qrout.apply(toom_add_n(j+2), ext_x2_b, temp_b)
    copy_qreg(qrout, x2, ext_x2_b, offset_dest=2)

    # res_m2
    copy_qreg(qrout, temp_b, res_m2)
    ext_x0 = qrout.new_wires(j+3)
    qrout.set_ancillae(ext_x0)
    copy_qreg(qrout, x0, ext_x0, offset_dest=3)
    qrout.apply(toom_sub_n(j+3), ext_x0, res_m2)
    copy_qreg(qrout, x0, ext_x0, offset_dest=3)

    # UNCOMPUTE
    copy_qreg(qrout, x2, ext_x2_b, offset_dest=2)
    qrout.apply(toom_add_n(j+2).dag(), ext_x2_b, temp_b)
    copy_qreg(qrout, x2, ext_x2_b, offset_dest=2)
    copy_qreg(qrout, res_m1, temp_b)

    copy_qreg(qrout, x2, ext_x2, offset_dest=1)
    qrout.apply(toom_add_n(j+1).dag(), ext_x2, temp_a)
    copy_qreg(qrout, x2, ext_x2, offset_dest=1)
    copy_qreg(qrout, x0, temp_a, offset_dest=1)

    return qrout


@build_gate("TOOM3_INTERP", [int])
def toom3_interp(n: int) -> QRoutine:
    """Interpolation block: reconstructs product polynomial coefficients."""
    qrout = QRoutine()
    j = n // 3
    p, q, r, s, t = [qrout.new_wires(k) for k in [2*j, 2*j+4, 2*j+4, 2*j+6, 2*j]]
    res_a, res_b, res_c, res_d, res_e = [qrout.new_wires(2*j+6) for _ in range(5)]

    copy_qreg(qrout, p, res_e, offset_dest=6)
    copy_qreg(qrout, t, res_a, offset_dest=6)

    i1_temp = qrout.new_wires(2*j+6)
    qrout.set_ancillae(i1_temp)
    i1 = qrout.new_wires(2*j+6)
    qrout.set_ancillae(i1)
    copy_qreg(qrout, s, i1_temp)
    ext_q = qrout.new_wires(2*j+6)
    qrout.set_ancillae(ext_q)
    copy_qreg(qrout, q, ext_q, offset_dest=2)
    qrout.apply(toom_sub_n(2*j+6), ext_q, i1_temp)

    # DIV
    inv3 = pow(3, -1, 2**(2*j+6))
    shifted_acc = qrout.new_wires(2*j+6)
    qrout.set_ancillae(shifted_acc)
    for i in range(2*j+6):
        if (inv3 >> i) & 1:
            copy_qreg(qrout, i1_temp, shifted_acc, offset_src=i, length=(2*j+6-i))
            qrout.apply(toom_add_n(2*j+6), shifted_acc, i1)
            copy_qreg(qrout, i1_temp, shifted_acc, offset_src=i, length=(2*j+6-i))

    i2 = qrout.new_wires(2*j+6)
    qrout.set_ancillae(i2)
    ext_r = qrout.new_wires(2*j+6)
    qrout.set_ancillae(ext_r)
    copy_qreg(qrout, r, ext_r, offset_dest=2)
    qrout.apply(CNOT, r[0], ext_r[1]) # Sign extension
    qrout.apply(CNOT, r[0], ext_r[0]) # Sign extension
    copy_qreg(qrout, ext_r, i2)
    ext_p = qrout.new_wires(2*j+6)
    qrout.set_ancillae(ext_p)
    copy_qreg(qrout, p, ext_p, offset_dest=6)
    qrout.apply(toom_sub_n(2*j+6), ext_p, i2)

    i3_temp = qrout.new_wires(2*j+6)
    qrout.set_ancillae(i3_temp)
    ext_q2 = qrout.new_wires(2*j+6)
    qrout.set_ancillae(ext_q2)
    copy_qreg(qrout, q, ext_q2, offset_dest=2)
    copy_qreg(qrout, ext_q2, i3_temp)
    qrout.apply(toom_sub_n(2*j+6), ext_r, i3_temp)

    i3 = qrout.new_wires(2*j+6)
    qrout.set_ancillae(i3)
    copy_qreg(qrout, i3_temp, i3, offset_dest=1, length=2*j+5)
    qrout.apply(CNOT, i3_temp[0], i3[0]) 

    res_b_temp = qrout.new_wires(2*j+6)
    qrout.set_ancillae(res_b_temp)
    copy_qreg(qrout, i2, res_b_temp)
    qrout.apply(toom_sub_n(2*j+6), i1, res_b_temp)
    
    copy_qreg(qrout, res_b_temp, res_b, offset_dest=1, length=2*j+5)
    qrout.apply(CNOT, res_b_temp[0], res_b[0]) 
    
    ext_2t = qrout.new_wires(2*j+6)
    qrout.set_ancillae(ext_2t)
    copy_qreg(qrout, t, ext_2t, offset_dest=5)
    qrout.apply(toom_add_n(2*j+6), ext_2t, res_b)

    copy_qreg(qrout, i3, res_c)
    qrout.apply(toom_add_n(2*j+6), i2, res_c)
    ext_t_c = qrout.new_wires(2*j+6)
    qrout.set_ancillae(ext_t_c)
    copy_qreg(qrout, t, ext_t_c, offset_dest=6)
    qrout.apply(toom_sub_n(2*j+6), ext_t_c, res_c)

    copy_qreg(qrout, i3, res_d)
    qrout.apply(toom_sub_n(2*j+6), res_b, res_d)

    # --- UNCOMPUTE ---
    copy_qreg(qrout, t, ext_t_c, offset_dest=6)
    
    qrout.apply(toom_sub_n(2*j+6).dag(), i1, res_b_temp)
    copy_qreg(qrout, i2, res_b_temp)
    
    qrout.apply(CNOT, i3_temp[0], i3[0])
    copy_qreg(qrout, i3_temp, i3, offset_dest=1, length=2*j+5)

    qrout.apply(toom_sub_n(2*j+6).dag(), ext_r, i3_temp)
    copy_qreg(qrout, ext_q2, i3_temp)
    copy_qreg(qrout, q, ext_q2, offset_dest=2)

    qrout.apply(toom_sub_n(2*j+6).dag(), ext_p, i2)
    copy_qreg(qrout, p, ext_p, offset_dest=6)
    copy_qreg(qrout, ext_r, i2)
    qrout.apply(CNOT, r[0], ext_r[0])
    qrout.apply(CNOT, r[0], ext_r[1])
    copy_qreg(qrout, r, ext_r, offset_dest=2)

    for i in range(2*j+6-1, -1, -1):
        if (inv3 >> i) & 1:
            copy_qreg(qrout, i1_temp, shifted_acc, offset_src=i, length=(2*j+6-i))
            qrout.apply(toom_add_n(2*j+6).dag(), shifted_acc, i1)
            copy_qreg(qrout, i1_temp, shifted_acc, offset_src=i, length=(2*j+6-i))

    qrout.apply(toom_sub_n(2*j+6).dag(), ext_q, i1_temp)
    copy_qreg(qrout, q, ext_q, offset_dest=2)
    copy_qreg(qrout, s, i1_temp)

    copy_qreg(qrout, t, ext_2t, offset_dest=5)

    return qrout


@build_gate("TOOM3_MULT", [int], arity=lambda n: 4*n)
def toom3_mult(n: int) -> QRoutine:
    """Main Toom-Cook 3 Multiplier routine."""
    qrout = QRoutine()
    j = n // 3
    x, y, res = qrout.new_wires(n), qrout.new_wires(n), qrout.new_wires(2*n)
    ev_x, ev_y = [qrout.new_wires(5*j+7) for _ in range(2)]
    qrout.apply(toom3_eval(n), x, ev_x)
    qrout.apply(toom3_eval(n), y, ev_y)
    x0, xinf, x1, xm1, xm2 = ev_x[0:j], ev_x[j:2*j], ev_x[2*j:3*j+2], ev_x[3*j+2:4*j+4], ev_x[4*j+4:]
    y0, yinf, y1, ym1, ym2 = ev_y[0:j], ev_y[j:2*j], ev_y[2*j:3*j+2], ev_y[3*j+2:4*j+4], ev_y[4*j+4:]
    p, t, q_val, r, s = (
        qrout.new_wires(2*j), qrout.new_wires(2*j), qrout.new_wires(2*j+4),
        qrout.new_wires(2*j+4), qrout.new_wires(2*j+6)
    )
    qrout.apply(toom_mult_prim(j, j, False, False), x0, y0, p)
    qrout.apply(toom_mult_prim(j, j, False, False), xinf, yinf, t)
    qrout.apply(toom_mult_prim(j+2, j+2, False, False), x1, y1, q_val)
    qrout.apply(toom_mult_prim(j+2, j+2, True, True), xm1, ym1, r)
    qrout.apply(toom_mult_prim(j+3, j+3, True, True), xm2, ym2, s)
    interp_res = qrout.new_wires(5*(2*j+6))
    qrout.set_ancillae(interp_res)
    qrout.apply(toom3_interp(n), p, q_val, r, s, t, interp_res)
    a, b, c, d, e = [interp_res[i*(2*j+6):(i+1)*(2*j+6)] for i in range(5)]

    def add_at_offset(src, dest, offset_j):
        m, k = len(dest), len(src)
        ext_size = m - offset_j
        if ext_size <= 0:
            return
        ext_src = qrout.new_wires(ext_size)
        qrout.set_ancillae(ext_src)
        actual = min(k, ext_size)
        for i in range(actual):
            qrout.apply(CNOT, src[k - actual + i], ext_src[ext_size - actual + i])
        
        qrout.apply(toom_add_n(ext_size), ext_src, dest[0:ext_size])
        for i in range(actual):
            qrout.apply(CNOT, src[k - actual + i], ext_src[ext_size - actual + i])

    add_at_offset(e, res, 0)
    add_at_offset(d, res, j)
    add_at_offset(c, res, 2*j)
    add_at_offset(b, res, 3*j)
    add_at_offset(a, res, 4*j)
    qrout.apply(toom3_interp(n).dag(), p, q_val, r, s, t, interp_res)
    qrout.apply(toom_mult_prim(j+3, j+3, True, True).dag(), xm2, ym2, s)
    qrout.apply(toom_mult_prim(j+2, j+2, True, True).dag(), xm1, ym1, r)
    qrout.apply(toom_mult_prim(j+2, j+2, False, False).dag(), x1, y1, q_val)
    qrout.apply(toom_mult_prim(j, j, False, False).dag(), xinf, yinf, t)
    qrout.apply(toom_mult_prim(j, j, False, False).dag(), x0, y0, p)
    qrout.apply(toom3_eval(n).dag(), y, ev_y)
    qrout.apply(toom3_eval(n).dag(), x, ev_x)
    return qrout
