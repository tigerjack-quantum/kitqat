# Author: Federico Pinto
import numpy as np
from qat.lang.AQASM.gates import CNOT, CCNOT, SWAP, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from qatext.qroutines.arith.cuccaro_arith import adder as cuccaro_adder

# --- Reversible Arithmetic Primitives for Montgomery ---

def copy_qreg(qrout, src, dest, offset_src=0, offset_dest=0, length=None):
    """
    Helper to copy a quantum register (or part of it) using CNOTs.
    |src>|dest> -> |src>|dest ^ src>
    """
    if length is None:
        length = len(src) - offset_src
    for i in range(length):
        qrout.apply(CNOT, src[offset_src + i], dest[offset_dest + i])

@build_gate("CONST_ADDER", [int, int, bool], arity=lambda n, val, dag: n + 1)
def const_adder_gate(n, val, dag=False):
    """
    In-place addition of a classical constant to a quantum register.
    |z> -> |z + val>
    """
    qrout = QRoutine()
    z_reg = qrout.new_wires(n + 1)
    
    # Allocate temporary register for the constant
    temp_const = qrout.new_wires(n)
    qrout.set_ancillae(temp_const)
    
    # Initialize temp_const with 'val'
    for i in range(n):
        if (val >> i) & 1:
            qrout.apply(X, temp_const[i])
            
    # Add temp_const to z_reg
    gate = cuccaro_adder(n, n + 1, False, True)
    if dag:
        gate = gate.dag()
    qrout.apply(gate, temp_const, z_reg)
    
    # Uncompute temp_const
    for i in range(n):
        if (val >> i) & 1:
            qrout.apply(X, temp_const[i])
            
    return qrout

@build_gate("MONTGOMERY_MULT_STEP", [int, int], arity=lambda n, p: 2 * n + 4)
def montgomery_step_gate(n, p):
    """
    A single step of the Montgomery multiplication (bit-by-bit).
    Implements: z = (z + x_i * y + m_i * p) / 2
    
    """
    qrout = QRoutine()
    xi = qrout.new_wires(1)
    y_reg = qrout.new_wires(n)
    z_reg = qrout.new_wires(n + 2)
    mi = qrout.new_wires(1)
    
    # z += x_i * y
    # Add n bits to n+2 bits
    qrout.apply(cuccaro_adder(n, n + 2, False, True).ctrl(), xi, y_reg, z_reg)
    
    #  m_i = z_0 (LSB of accumulator)
    qrout.apply(CNOT, z_reg[0], mi)
    
    # z += m_i * p
    # Controlled constant addition: add n bits to n+2 bits
    # Allocate temporary register for the constant p
    temp_const = qrout.new_wires(n)
    qrout.set_ancillae(temp_const)
    for i in range(n):
        if (p >> i) & 1:
            qrout.apply(X, temp_const[i])
            
    qrout.apply(cuccaro_adder(n, n + 2, False, True).ctrl(), mi, temp_const, z_reg)
    
    # Uncompute temp_const
    for i in range(n):
        if (p >> i) & 1:
            qrout.apply(X, temp_const[i])
    
    # z >>= 1 (Division by 2)
    # We swap up to n+1 to shift all bits including the carry
    for j in range(n + 1):
        qrout.apply(SWAP, z_reg[j], z_reg[j+1])
        
    return qrout

@build_gate("MONTGOMERY_MULT", [int, int], arity=lambda n, p: 3 * n)
def montgomery_mult(n, p):
    """
    Quantum Montgomery Multiplication.
    
    """
    qrout = QRoutine()
    x_reg = qrout.new_wires(n)
    y_reg = qrout.new_wires(n)
    out_reg = qrout.new_wires(n)
    
    # Logic is easier with LSB-first
    lx = x_reg[::-1]
    ly = y_reg[::-1]
    lout = out_reg[::-1]
    
    # Internal Accumulator (n+2 bits to avoid overflow)
    z_reg = qrout.new_wires(n + 2)
    qrout.set_ancillae(z_reg)
    lz = z_reg[::-1] # lz[0] is LSB
    
    # Montgomery bits (n bits to store the choices m_i for reversibility)
    m_reg = qrout.new_wires(n)
    qrout.set_ancillae(m_reg)
    lm = m_reg[::-1]
    
    # --- FORWARD PASS ---
    step_gate = montgomery_step_gate(n, p)
    for i in range(n):
        qrout.apply(step_gate, lx[i], ly, lz, lm[i])
        
    # --- MODULAR CORRECTION (z = z mod p) ---
    # Result R is in lz, 0 <= R < 2p.
    # z -= p
    # To subtract p (n bits) from z (n+2 bits)
    temp_p = qrout.new_wires(n)
    qrout.set_ancillae(temp_p)
    for i in range(n):
        if (p >> i) & 1:
            qrout.apply(X, temp_p[i])
    qrout.apply(cuccaro_adder(n, n + 2, False, True).dag(), temp_p, lz)
    
    # Check if negative: lz[n+1] is the MSB of n+2 bits
    corr_bit = qrout.new_wires(1)
    qrout.set_ancillae(corr_bit)
    qrout.apply(X, corr_bit)
    qrout.apply(CNOT, lz[n + 1], corr_bit) # corr_bit = 1 if z >= 0, 0 if z < 0
    
    # Restore if negative (corr_bit == 0)
    qrout.apply(X, corr_bit)
    qrout.apply(cuccaro_adder(n, n + 2, False, True).ctrl(), corr_bit, temp_p, lz)
    qrout.apply(X, corr_bit)
    
    # After correction, result is in the first n bits of lz.
    copy_qreg(qrout, lz, lout, length=n)
    
    # --- UNCOMPUTE CORRECTION ---
    qrout.apply(X, corr_bit)
    qrout.apply(cuccaro_adder(n, n + 2, False, True).ctrl().dag(), corr_bit, temp_p, lz)
    qrout.apply(X, corr_bit)
    qrout.apply(CNOT, lz[n + 1], corr_bit)
    qrout.apply(X, corr_bit)
    qrout.apply(cuccaro_adder(n, n + 2, False, True), temp_p, lz)
    for i in range(n):
        if (p >> i) & 1:
            qrout.apply(X, temp_p[i])
            
    # --- BACKWARD PASS (Uncompute) ---
    for i in range(n - 1, -1, -1):
        qrout.apply(step_gate.dag(), lx[i], ly, lz, lm[i])
        
    return qrout

# --- Conversion to/from Montgomery Representation ---

@build_gate("MONTGOMERY_FORM", [int, int], arity=lambda n, p: 2 * n)
def montgomery_form(n, p):
    """
    Converts |x> to its Montgomery representation |x * 2^n mod p>.
    Uses the property: REDC(x, 2^(2n) mod p) = x * 2^(2n) * 2^-n = x * 2^n mod p.
    """
    qrout = QRoutine()
    x_reg = qrout.new_wires(n)
    res_reg = qrout.new_wires(n)
    
    # R^2 = 2^(2n) mod p
    r2 = pow(2, 2 * n, p)
    
    # Create a constant register for R^2
    r2_reg = qrout.new_wires(n)
    qrout.set_ancillae(r2_reg)
    for i in range(n):
        if (r2 >> (n - 1 - i)) & 1: # Big-endian
            qrout.apply(X, r2_reg[i])
            
    qrout.apply(montgomery_mult(n, p), x_reg, r2_reg, res_reg)
    
    # Uncompute r2_reg
    for i in range(n):
        if (r2 >> (n - 1 - i)) & 1:
            qrout.apply(X, r2_reg[i])
            
    return qrout

@build_gate("MONTGOMERY_RES", [int, int], arity=lambda n, p: 2 * n)
def montgomery_res(n, p):
    """
    Converts from Montgomery representation |x' = x * 2^n mod p> back to |x>.
    Uses the property: REDC(x', 1) = x * 2^n * 1 * 2^-n = x mod p.
    """
    qrout = QRoutine()
    x_prime_reg = qrout.new_wires(n)
    res_reg = qrout.new_wires(n)
    
    # Constant 1 register
    one_reg = qrout.new_wires(n)
    qrout.set_ancillae(one_reg)
    qrout.apply(X, one_reg[n-1]) # Big-endian LSB is at the end
    
    qrout.apply(montgomery_mult(n, p), x_prime_reg, one_reg, res_reg)
    
    # Uncompute one_reg
    qrout.apply(X, one_reg[n-1])
    
    return qrout
