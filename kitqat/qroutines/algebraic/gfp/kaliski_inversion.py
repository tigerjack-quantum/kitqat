__authors__ = [
    "Federico Pinto <federico.pinto@mail.polimi.it>",
    "Simone Perriello <sperriello@proton.me>",
]

from qat.lang.AQASM.gates import CCNOT, CNOT, SWAP, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from kitqat.qroutines.arith.cuccaro_arith import adder as cuccaro_adder


def copy_qreg(qrout, src, dest, offset_src=0, offset_dest=0, length=None):
    if length is None:
        length = min(len(src) - offset_src, len(dest) - offset_dest)
    for i in range(length):
        qrout.apply(CNOT, src[offset_src + i], dest[offset_dest + i])

@build_gate("KALISKI_ROUND", [int], arity=lambda n: 5 * n + 4)
def mk_round(nbits: int) -> QRoutine:
    qf = QRoutine()
    # Inputs
    u = qf.new_wires(nbits)
    v = qf.new_wires(nbits)
    r = qf.new_wires(nbits + 1)
    s = qf.new_wires(nbits + 1)
    k = qf.new_wires(nbits)
    f = qf.new_wires(1)
    m_i = qf.new_wires(1)

    # Ancillae for branch evaluation
    a = qf.new_wires(1)
    u_even = qf.new_wires(1)
    v_even = qf.new_wires(1)
    both_odd = qf.new_wires(1)
    u_gt_v = qf.new_wires(1)
    temp_v_copy = qf.new_wires(nbits + 1)

    qf.set_ancillae(a, u_even, v_even, both_odd, u_gt_v, temp_v_copy)

    # 1. Evaluate primitive conditions (Uncontrolled)
    # Big Endian: index nbits-1 is LSB for nbits size arrays
    qf.apply(X, u[nbits-1])
    qf.apply(CNOT, u[nbits-1], u_even[0])
    qf.apply(X, u[nbits-1])

    qf.apply(X, v[nbits-1])
    qf.apply(CNOT, v[nbits-1], v_even[0])
    qf.apply(X, v[nbits-1])

    qf.apply(X, u_even[0])
    qf.apply(X, v_even[0])
    qf.apply(CCNOT, u_even[0], v_even[0], both_odd[0])
    qf.apply(X, u_even[0])
    qf.apply(X, v_even[0])

    copy_qreg(qf, v, temp_v_copy, offset_dest=1)
    adder_comp = cuccaro_adder(nbits, nbits + 1, False, False)
    qf.apply(adder_comp.dag(), u, temp_v_copy)
    qf.apply(CCNOT, both_odd[0], temp_v_copy[0], u_gt_v[0])

    # 2. Encode to 'a' and 'b' (m_i), controlled by f
    # a = f AND (u_even OR u_gt_v)
    qf.apply(CCNOT, f[0], u_even[0], a[0])
    qf.apply(CCNOT, f[0], u_gt_v[0], a[0])

    # m_i = f AND ((NOT u_even AND v_even) OR u_gt_v)
    not_u_and_v = qf.new_wires(1)
    qf.set_ancillae(not_u_and_v)
    qf.apply(X, u_even[0])
    qf.apply(CCNOT, u_even[0], v_even[0], not_u_and_v[0])
    qf.apply(X, u_even[0])

    qf.apply(CCNOT, f[0], not_u_and_v[0], m_i[0])
    qf.apply(CCNOT, f[0], u_gt_v[0], m_i[0])

    # Uncompute not_u_and_v
    qf.apply(X, u_even[0])
    qf.apply(CCNOT, u_even[0], v_even[0], not_u_and_v[0])
    qf.apply(X, u_even[0])

    # 3. Immediately Uncompute primitive conditions BEFORE arithmetic dispatch
    qf.apply(CCNOT, both_odd[0], temp_v_copy[0], u_gt_v[0])
    qf.apply(adder_comp, u, temp_v_copy)
    for i in range(nbits):
        qf.apply(CNOT, v[i], temp_v_copy[i + 1])

    qf.apply(X, u_even[0])
    qf.apply(X, v_even[0])
    qf.apply(CCNOT, u_even[0], v_even[0], both_odd[0])
    qf.apply(X, u_even[0])
    qf.apply(X, v_even[0])

    qf.apply(X, v[nbits-1])
    qf.apply(CNOT, v[nbits-1], v_even[0])
    qf.apply(X, v[nbits-1])

    qf.apply(X, u[nbits-1])
    qf.apply(CNOT, u[nbits-1], u_even[0])
    qf.apply(X, u[nbits-1])

    # 4. Arithmetic Dispatch (Controlled by 'a', 'm_i' and 'f')
    branch_00 = qf.new_wires(1)
    branch_01 = qf.new_wires(1)
    branch_10 = qf.new_wires(1)
    branch_11 = qf.new_wires(1)
    qf.set_ancillae(branch_00, branch_01, branch_10, branch_11)

    qf.apply(X, a[0])
    qf.apply(X, m_i[0])
    qf.apply(CCNOT, a[0], m_i[0], branch_00[0])
    qf.apply(X, m_i[0])
    qf.apply(CCNOT, a[0], m_i[0], branch_01[0])
    qf.apply(X, a[0])
    qf.apply(X, m_i[0])
    qf.apply(CCNOT, a[0], m_i[0], branch_10[0])
    qf.apply(X, m_i[0])
    qf.apply(CCNOT, a[0], m_i[0], branch_11[0])

    f_b00 = qf.new_wires(1)
    f_b01 = qf.new_wires(1)
    f_b10 = qf.new_wires(1)
    f_b11 = qf.new_wires(1)
    qf.set_ancillae(f_b00, f_b01, f_b10, f_b11)

    qf.apply(CCNOT, f[0], branch_00[0], f_b00[0])
    qf.apply(CCNOT, f[0], branch_01[0], f_b01[0])
    qf.apply(CCNOT, f[0], branch_10[0], f_b10[0])
    qf.apply(CCNOT, f[0], branch_11[0], f_b11[0])

    u_pad = qf.new_wires(1)
    v_pad = qf.new_wires(1)
    r_pad = qf.new_wires(1)
    s_pad = qf.new_wires(1)
    qf.set_ancillae(u_pad, v_pad, r_pad, s_pad)

    u_ext = [u_pad[0]] + list(u)
    v_ext = [v_pad[0]] + list(v)
    r_ext = [r_pad[0]] + list(r)
    s_ext = [s_pad[0]] + list(s)

    adder_uv = cuccaro_adder(nbits, nbits + 1, False, False)
    adder_rs = cuccaro_adder(nbits + 1, nbits + 2, False, False)

    qf.apply(adder_uv.dag().ctrl(), f_b11[0], v, u_ext)
    qf.apply(adder_rs.ctrl(), f_b11[0], s, r_ext)

    qf.apply(adder_uv.dag().ctrl(), f_b00[0], u, v_ext)
    qf.apply(adder_rs.ctrl(), f_b00[0], r, s_ext)

    shift_u = qf.new_wires(1)
    shift_v = qf.new_wires(1)
    qf.set_ancillae(shift_u, shift_v)
    qf.apply(CNOT, f_b10[0], shift_u[0])
    qf.apply(CNOT, f_b11[0], shift_u[0])
    qf.apply(CNOT, f_b01[0], shift_v[0])
    qf.apply(CNOT, f_b00[0], shift_v[0])

    for i in range(nbits - 1, 0, -1):
        qf.apply(SWAP.ctrl(), shift_u[0], u[i], u[i-1])
        qf.apply(SWAP.ctrl(), shift_v[0], v[i], v[i-1])

    for i in range(0, nbits):
        qf.apply(SWAP.ctrl(), shift_u[0], s[i], s[i+1])
        qf.apply(SWAP.ctrl(), shift_v[0], r[i], r[i+1])

    qf.apply(CNOT, f_b10[0], shift_u[0])
    qf.apply(CNOT, f_b11[0], shift_u[0])
    qf.apply(CNOT, f_b01[0], shift_v[0])
    qf.apply(CNOT, f_b00[0], shift_v[0])

    qf.apply(CCNOT, f[0], branch_00[0], f_b00[0])
    qf.apply(CCNOT, f[0], branch_01[0], f_b01[0])
    qf.apply(CCNOT, f[0], branch_10[0], f_b10[0])
    qf.apply(CCNOT, f[0], branch_11[0], f_b11[0])

    qf.apply(X, a[0])
    qf.apply(X, m_i[0])
    qf.apply(CCNOT, a[0], m_i[0], branch_00[0])
    qf.apply(X, m_i[0])
    qf.apply(CCNOT, a[0], m_i[0], branch_01[0])
    qf.apply(X, a[0])
    qf.apply(X, m_i[0])
    qf.apply(CCNOT, a[0], m_i[0], branch_10[0])
    qf.apply(X, m_i[0])
    qf.apply(CCNOT, a[0], m_i[0], branch_11[0])

    # 5. Uncompute 'a'
    qf.apply(CCNOT, f[0], r[nbits], a[0])

    # 6. Termination check: f -> 0 if v is 0 AND k is 0
    # This ensures f only flips ONCE, when v reaches 0 for the first time.
    v_is_zero = qf.new_wires(1)
    k_is_zero = qf.new_wires(1)
    qf.set_ancillae(v_is_zero, k_is_zero)

    for i in range(nbits):
        qf.apply(X, v[i])
        qf.apply(X, k[i])

    qf.apply(X.ctrl(nbits), v, v_is_zero[0])
    qf.apply(X.ctrl(nbits), k, k_is_zero[0])

    for i in range(nbits):
        qf.apply(X, v[i])
        qf.apply(X, k[i])

    qf.apply(CCNOT, v_is_zero[0], k_is_zero[0], f[0])

    # Uncompute
    for i in range(nbits):
        qf.apply(X, v[i])
        qf.apply(X, k[i])

    qf.apply(X.ctrl(nbits), v, v_is_zero[0])
    qf.apply(X.ctrl(nbits), k, k_is_zero[0])

    for i in range(nbits):
        qf.apply(X, v[i])
        qf.apply(X, k[i])

    # 7. Counter increment
    not_f = qf.new_wires(1)
    qf.set_ancillae(not_f)
    qf.apply(X, f[0])
    qf.apply(CNOT, f[0], not_f[0])
    qf.apply(X, f[0])

    carries = qf.new_wires(nbits)
    qf.set_ancillae(carries)

    qf.apply(CNOT, not_f[0], carries[nbits-1])
    for i in range(nbits-1, 0, -1):
        qf.apply(CCNOT, carries[i], k[i], carries[i-1])
    for i in range(0, nbits):
        qf.apply(CNOT, carries[i], k[i])
    for i in range(1, nbits):
        qf.apply(CCNOT, carries[i], k[i], carries[i-1])
    qf.apply(CNOT, not_f[0], carries[nbits-1])

    qf.apply(X, f[0])
    qf.apply(CNOT, f[0], not_f[0])
    qf.apply(X, f[0])

    return qf

@build_gate("KALISKI_BLOCK", [int], arity=lambda n: 5 * n + 4 + 2 * n - 1)
def kaliski_block(nbits: int) -> QRoutine:
    qf = QRoutine()
    u = qf.new_wires(nbits)
    v = qf.new_wires(nbits)
    r = qf.new_wires(nbits + 1)
    s = qf.new_wires(nbits + 1)
    k = qf.new_wires(nbits)
    f = qf.new_wires(1)
    m = qf.new_wires(2 * nbits) # The 2n history qubits

    round_gate = mk_round(nbits)
    for i in range(2 * nbits):
        qf.apply(round_gate, u, v, r, s, k, f, m[i])
    return qf
