__author__ = "Federico Pinto <federico.pinto@mail.polimi.it>"
# Author: Federico Pinto
import math
from qat.lang.AQASM.gates import X, CNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from qatext.qroutines.arith.cuccaro_arith import adder as cuccaro_adder
from qatext.qatmgmt.routines import QRoutineWrapper

def _get_const_add_gate(val, n_acc):
    """
    Helper gate for adding a classical constant to a quantum register.
    Uses a temporary garbage qubit to safely absorb the carry-out,
    """
    val = val & ((1 << n_acc) - 1)
    
    @build_gate("CONST_ADD", [int, int])
    def const_add_routine(v, n):
        rout = QRoutine()
        target = rout.new_wires(n)
        anc = rout.new_wires(n)
        rout.set_ancillae(anc)
        
        garbage_cout = rout.new_wires(1)
        rout.set_ancillae(garbage_cout)
        
        target_padded = list(target[::-1]) + [garbage_cout[0]]
        
        # Initialize in Little-Endian (LSB at anc[0])
        for j in range(n):
            if (v >> j) & 1:
                rout.apply(X, anc[j])
                
        gate = cuccaro_adder(n, n, False, True)
        rout.apply(gate, anc, target_padded)
        
        # Uncompute ancilla
        for j in range(n):
            if (v >> j) & 1:
                rout.apply(X, anc[j])
        return rout
        
    return const_add_routine(val, n_acc)

def q_c_mult_add(prog, qreg_in, qreg_acc, c_val, dag=False):
    """
    Adds (val(qreg_in) * c_val) to qreg_acc using controlled constant additions.
    Follows big-endian convention (qreg_in[0] is MSB).
    """
    n_in = len(qreg_in)
    n_acc = len(qreg_acc)
    for i in range(n_in):
        qubit = qreg_in[n_in - 1 - i]
        
        term = (c_val << i) & ((1 << n_acc) - 1)
        
        if term == 0:
            continue
            
        add_gate = _get_const_add_gate(term, n_acc)
        if dag:
            add_gate = add_gate.dag()
        prog.apply(add_gate.ctrl(), qubit, qreg_acc)

@build_gate("BARRETT_REDUCTION", [int, int], arity=lambda n, N: 3 * n)
def barrett_reduction(n, N):
    """
    Optimized Folding Barrett Reduction 
    Computes r = t mod N for a 2n-bit t and n-bit N.
    """
    qroutw = QRoutineWrapper(QRoutine())
    t_reg = qroutw.new_wires(2 * n)
    out_reg = qroutw.new_wires(n)
    
    s = n // 2
    n_folded_const = pow(2, 3 * s, N)
    mu = (2**(3 * s + 3)) // N
    
    # Internal registers (ancillae)
    t_prime_size = 3 * s + 2
    t_prime = qroutw.qarray_wires(1, t_prime_size, "t_prime", int)[0]
    qroutw.set_ancillae(t_prime)
    
    p_size = 2 * s + 9
    p_reg = qroutw.qarray_wires(1, p_size, "p_reg", int)[0]
    qroutw.set_ancillae(p_reg)
    
    corr_bit = qroutw.new_wires(1)[0]
    qroutw.set_ancillae(corr_bit)
    
    # --- FORWARD PASS ---
    # Folding Stage: t' = (t mod 2^3s) + floor(t / 2^3s) * N'
    for i in range(3 * s):
        qroutw.apply(CNOT, t_reg[2 * n - 3 * s + i], t_prime[t_prime_size - 3 * s + i])
    q_c_mult_add(qroutw, t_reg[:2 * n - 3 * s], t_prime, n_folded_const)
    
    # Reduction Stage: q_hat = floor(floor(t' / 2^(2s-2)) * mu / 2^(s+5))
    q_c_mult_add(qroutw, t_prime[:s + 4], p_reg, mu)
    q_hat_size = p_size - (s + 5)
    q_hat = p_reg[:q_hat_size]
    # R = t' - q_hat * N
    q_c_mult_add(qroutw, q_hat, t_prime, N, dag=True)
    
    # Correction Stage: if R >= N then R = R - N
    # Use n+2 bits of t_prime to detect sign correctly
    r_reg = t_prime[t_prime_size - (n + 2):]
    sub_gate = _get_const_add_gate(N, n + 2)
    qroutw.apply(sub_gate.dag(), r_reg)
    
    # If MSB is 0, R-N was positive (R >= N). If MSB is 1, R < N.
    # restoration: if MSB is 1, add N back.
    qroutw.apply(CNOT, r_reg[0], corr_bit)
    qroutw.apply(sub_gate.ctrl(), corr_bit, r_reg)
    
    # Copy final result to output
    for i in range(n):
        qroutw.apply(CNOT, r_reg[2 + i], out_reg[i])
        
    # --- BACKWARD PASS (Uncompute) ---
    qroutw.apply(sub_gate.ctrl().dag(), corr_bit, r_reg)
    qroutw.apply(CNOT, r_reg[0], corr_bit)
    qroutw.apply(sub_gate, r_reg)
    
    q_c_mult_add(qroutw, q_hat, t_prime, N)
    q_c_mult_add(qroutw, t_prime[:s + 4], p_reg, mu, dag=True)
    
    q_c_mult_add(qroutw, t_reg[:2 * n - 3 * s], t_prime, n_folded_const, dag=True)
    for i in range(3 * s):
        qroutw.apply(CNOT, t_reg[2 * n - 3 * s + i], t_prime[t_prime_size - 3 * s + i])
        
    return qroutw
