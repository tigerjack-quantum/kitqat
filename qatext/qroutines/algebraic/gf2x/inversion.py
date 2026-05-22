# Author: Federico Pinto
from qat.lang.AQASM.gates import CNOT, CCNOT,SWAP
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

@build_gate("SQUARE_MOD", [int, int], arity=lambda n, m_bits: 2 * n)
def square_mod(n: int, m_bits: int) -> QRoutine:
    """
    Squares a polynomial modulo m(z) in F_2[z].
    Target register is initially |0>.
    Input is the first n wires, output is the second n wires.
    """
    qrout = QRoutine()
    reg_in = qrout.new_wires(n)
    reg_out = qrout.new_wires(n)
    
    for i in range(n):
        # 2*i can exceed n-1, so we must reduce z^(2i) mod m(z)
        # For a minimal implementation, let's calculate the reduction classically
        # and apply CNOTs.
        val = 1 << (2 * i)
        # classical polynomial reduction
        while val >= (1 << n):
            # find highest degree of val
            deg = val.bit_length() - 1
            # subtract (XOR) m(z) shifted by (deg - n)
            val ^= (m_bits << (deg - n))
            
        for j in range(n):
            if (val >> j) & 1:
                qrout.apply(CNOT, reg_in[i], reg_out[j])
                
    return qrout
@build_gate("MODMULT", [int, int], arity=lambda n, m_bits: 3 * n)
def modmult(n: int, m_bits: int) -> QRoutine:
    """
    In-place modular multiplication: C <- C + A * B mod m(z).
    Input: A (n wires), B (n wires), C (n wires).
    """
    qrout = QRoutine()
    reg_a = qrout.new_wires(n)
    reg_b = qrout.new_wires(n)
    reg_c = qrout.new_wires(n)
    
    for i in range(n):
        for j in range(n):
            val = 1 << (i + j)
            while val >= (1 << n):
                deg = val.bit_length() - 1
                val ^= (m_bits << (deg - n))
            
            for k in range(n):
                if (val >> k) & 1:
                    qrout.apply(CCNOT, reg_a[i], reg_b[j], reg_c[k])
                    
    return qrout

@build_gate("FLT_UNCOMPUTE_1_16", [int, int, int], arity=lambda n, m_bits, k_val: (k_val + 1) * n)
def flt_uncompute_1_16(n: int, m_bits: int, k_val: int) -> QRoutine:
    qrout = QRoutine()
    f_arr = [qrout.new_wires(n) for _ in range(k_val + 1)]
    
    val = n - 1
    k_seq = []
    bit_pos = 0
    while val > 0:
        if val & 1:
            k_seq.append(bit_pos)
        val >>= 1
        bit_pos += 1
    k_seq.reverse() 
    t = len(k_seq)
    k1 = k_seq[0]
    
    def copy_reg(src, dst):
        for w1, w2 in zip(src, dst):
            qrout.apply(CNOT, w1, w2)

    def apply_square(tgt):
        tmp = qrout.new_wires(n)
        qrout.set_ancillae(tmp)
        qrout.apply(square_mod(n, m_bits), tgt, tmp)
        for i in range(n):
            qrout.apply(SWAP, tgt[i], tmp[i])
            
        if n == 1:
            for i in range(n):
                qrout.apply(CNOT, tgt[i], tmp[i])
            return

        squares = [tgt]
        new_temps = []
        for i in range(n - 1):
            sq_tmp = qrout.new_wires(n)
            qrout.set_ancillae(sq_tmp)
            new_temps.append(sq_tmp)
            qrout.apply(square_mod(n, m_bits), squares[-1], sq_tmp)
            squares.append(sq_tmp)
            
        for i in range(n):
            qrout.apply(CNOT, squares[-1][i], tmp[i])
            
        for i in range(n - 2, -1, -1):
            qrout.apply(square_mod(n, m_bits).dag(), squares[i], new_temps[i])
            
    def apply_inv_square(tgt):
        for _ in range(n - 1):
            apply_square(tgt)
            
    # lines 1-16
    for i in range(1, k1 + 1):
        copy_reg(f_arr[i-1], f_arr[k_val])
        for _ in range(2**(i-1)):
            apply_square(f_arr[k_val])
        qrout.apply(modmult(n, m_bits), f_arr[i-1], f_arr[k_val], f_arr[i])
        for _ in range(2**(i-1)):
            apply_inv_square(f_arr[k_val])
        copy_reg(f_arr[i-1], f_arr[k_val])
        
    for s in range(1, t):
        for i in range(1, 2**(k_seq[s]) + 1):
            copy_reg(f_arr[k1+s-1], f_arr[k1+s])
            apply_square(f_arr[k1+s])
            copy_reg(f_arr[k1+s], f_arr[k1+s-1])
        qrout.apply(modmult(n, m_bits), f_arr[k1+s-1], f_arr[k_seq[s]], f_arr[k1+s])
        
    if t == 1:
        for w1, w2 in zip(f_arr[k1], f_arr[k_val]):
            qrout.apply(SWAP, w1, w2)
    
    apply_square(f_arr[k_val])

    return qrout

@build_gate("FLT_DIV", [int, int], arity=lambda n, m_bits: 3 * n)
def flt_div(n: int, m_bits: int) -> QRoutine:
    qrout = QRoutine()
    f0 = qrout.new_wires(n)
    B = qrout.new_wires(n)
    C = qrout.new_wires(n)
    
    if n <= 1:
        for i in range(n):
            qrout.apply(CCNOT, f0[i], B[i], C[i])
        return qrout

    val = n - 1
    k_seq = []
    bit_pos = 0
    while val > 0:
        if val & 1:
            k_seq.append(bit_pos)
        val >>= 1
        bit_pos += 1
    k_seq.reverse() 
    t = len(k_seq)
    k1 = k_seq[0]
    k = max(k1 + t - 1, k1 + 1)
    
    anc_wires = qrout.new_wires(k * n)
    qrout.set_ancillae(anc_wires)
    
    uncomp_1_16 = flt_uncompute_1_16(n, m_bits, k)
    qrout.apply(uncomp_1_16, f0, anc_wires)
    
    qrout.apply(modmult(n, m_bits), anc_wires[(k-1)*n : k*n], B, C)
    
    qrout.apply(uncomp_1_16.dag(), f0, anc_wires)

    return qrout


