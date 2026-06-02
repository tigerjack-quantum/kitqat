__author__ = "Federico Pinto <federico.pinto@mail.polimi.it>"
# Author: Federico Pinto
from qat.lang.AQASM.gates import CNOT, CCNOT, X, SWAP
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from kitqat.qroutines.arith.cuccaro_arith import adder as cuccaro_adder
from kitqat.qroutines.algebraic.gf2x.adders import cuccaro_adder_int
from kitqat.qroutines.arith.cuccaro_arith import adder as cuccaro_adder


@build_gate("ADDER2BIT", [])
def adder2bit() -> QRoutine:
    qrout = QRoutine()
    
    reg_a = qrout.new_wires(1)
    reg_b = qrout.new_wires(1)
    
    qrout.apply(CNOT, reg_a[0], reg_b[0])
        
    return qrout

sub2bit = adder2bit

@build_gate("MUL2BIT", [], arity=3)
def mul2bit() -> QRoutine:
    qrout = QRoutine()
   
    reg_a = qrout.new_wires(1)
    reg_b = qrout.new_wires(1)
    reg_out = qrout.new_wires(1)
    
    qrout.apply(CCNOT, reg_a[0], reg_b[0], reg_out[0])
        
    return qrout

@build_gate("ADDERNBIT", [int], arity=lambda n: n * 2)
def adder_n_bit(n: int) -> QRoutine:
    """
    N-bit adder for GF(2^m) polynomials.
    It performs the bitwise XOR operation: |a>|b> -> |a>|a XOR b>.
    """
    qrout = QRoutine()
    
    # Allocate two quantum registers of size n
    reg_a = qrout.new_wires(n)
    reg_b = qrout.new_wires(n)
    
    # Apply CNOT gate pair by pair (bitwise XOR)
    for i in range(n):
        qrout.apply(CNOT, reg_a[i], reg_b[i])
        
    return qrout


sub_n_bit = adder_n_bit

@build_gate("MUL_N_BIT", [int], arity=lambda n: n * 4)
def mul_n_bit(n: int) -> QRoutine:
    
    
    qrout = QRoutine()
    
    # Allocate registers
    reg_a = qrout.new_wires(n)
    reg_b = qrout.new_wires(n)
    reg_out = qrout.new_wires(n * 2) 
    
    # Double loop for the schoolbook multiplication
    for i in range(n):
        for j in range(n):
            qrout.apply(CCNOT, reg_a[i], reg_b[j], reg_out[i + j])
            
    return qrout

@build_gate("SCHOOLBOOK_RED", [int, int], arity=lambda n, m_bits: 2 * n)
def schoolbook_reduction(n: int, m_bits: int) -> QRoutine:
    """
    Schoolbook modular reduction for GF(2^m) polynomials.
    Reduces a 2n-bit polynomial modulo an n-degree polynomial (m_bits).
    The remainder is stored in the lower n bits, and the quotient in the upper n bits.
    """
    qrout = QRoutine()
    reg = qrout.new_wires(2 * n)
    
    # Polynomial division
    for i in range(2 * n - 1, n - 1, -1):
        for j in range(n):
            if (m_bits >> j) & 1:
                qrout.apply(CNOT, reg[i], reg[i - n + j])
                
    return qrout

@build_gate("SCHOOLBOOK_RED_INT", [int, int], arity=lambda n, N_val: 2 * n + (n + 1))
def schoolbook_reduction_int(n: int, N_val: int) -> QRoutine:
    """
    Schoolbook modular reduction for integers using Restoring Division.
    Computes t mod N for a 2n-bit t and n-bit N.
    The remainder is stored in the 2n-bit register and the inverted quotient in the (n+1)-bit register.
    """
    qrout = QRoutine()
    t_reg = qrout.new_wires(2 * n)
    res_couts = qrout.new_wires(n + 1)

    borrows = qrout.new_wires(n + 1)
    qrout.set_ancillae(borrows)

    for i in range(n, -1, -1):
        val_to_sub = N_val << i
        if val_to_sub == 0 or val_to_sub >= (1 << (2 * n)):
            continue

        val_to_add = (1 << (2 * n)) - val_to_sub

        c_reg = qrout.new_wires(2 * n)
        qrout.set_ancillae(c_reg)
        
        for j in range(2 * n):
            if (val_to_add >> (2 * n - 1 - j)) & 1:
                qrout.apply(X, c_reg[j])

        borrow = borrows[i:i+1]
        res_cout = res_couts[i:i+1]
        add_gate = cuccaro_adder_int(2 * n, 2 * n, True)
        qrout.apply(add_gate, c_reg, t_reg, borrow)

        
        qrout.apply(X, borrow[0])

        c_restore = qrout.new_wires(2 * n)
        qrout.set_ancillae(c_restore)

        for j in range(2 * n):
            if (val_to_sub >> (2 * n - 1 - j)) & 1:
                qrout.apply(CNOT, borrow[0], c_restore[j])

        
        qrout.apply(add_gate, c_restore, t_reg, res_cout)

        for j in range(2 * n):
            if (val_to_sub >> (2 * n - 1 - j)) & 1:
                qrout.apply(CNOT, borrow[0], c_restore[j])

        
        qrout.apply(CNOT, res_cout[0], borrow[0])

        
        for j in range(2 * n):
            if (val_to_add >> (2 * n - 1 - j)) & 1:
                qrout.apply(X, c_reg[j])

    return qrout