
import math
from qat.lang.AQASM.gates import CNOT, CCNOT, X, H, SWAP, PH
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine


# --- CUCCARO ADDER COMPONENTS ---

@build_gate("MAJ", [], arity=3)
def _maj():
    """Majority gate: (c, b, a) -> (c^a, b^a, Maj(c,b,a))"""
    qrout = QRoutine()
    c, b, a = qrout.new_wires(3)
    qrout.apply(CNOT, a, b)
    qrout.apply(CNOT, a, c)
    qrout.apply(CCNOT, c, b, a)
    return qrout

@build_gate("UMA", [], arity=3)
def _uma():
    """Unmajority and Add gate."""
    qrout = QRoutine()
    c, b, a = qrout.new_wires(3)
    qrout.apply(X, b)
    qrout.apply(CNOT, c, b)
    qrout.apply(CCNOT, c, b, a)
    qrout.apply(X, b)
    qrout.apply(CNOT, a, c)
    qrout.apply(CNOT, a, b)
    return qrout

@build_gate("CUCCARO_ADD", [int, int, bool], arity=lambda al, bl, ov: al + bl + (1 if ov else 0))
def cuccaro_adder_int(a_len: int, b_len: int, overflow_qubit: bool = False):
    """
    Cuccaro ripple-carry adder.
    Performs |a>|b> -> |a>|a+b> (mod 2^b_len or with overflow).
    Implementation uses the MAJ/UMA structure.
    """
    qrout = QRoutine()
    a_orig = qrout.new_wires(a_len)
    b_orig = qrout.new_wires(b_len)
    
    n = max(a_len, b_len)
    a_rev = list(reversed(a_orig))
    b_rev = list(reversed(b_orig))
    
    # Generalization: Pad with virtual zeros (ancillae) to match max length
    if a_len < n:
        a_pad = qrout.new_wires(n - a_len)
        qrout.set_ancillae(a_pad)
        a_rev += list(a_pad)
    if b_len < n:
        b_pad = qrout.new_wires(n - b_len)
        qrout.set_ancillae(b_pad)
        b_rev += list(b_pad)
        
    cin = qrout.new_wires(1)
    qrout.set_ancillae(cin)
    
    if overflow_qubit:
        cout = qrout.new_wires(1)
        # Cuccaro logic for overflow
        qrout.apply(_maj(), cin[0], b_rev[0], a_rev[0])
        for i in range(1, n):
            qrout.apply(_maj(), a_rev[i-1], b_rev[i], a_rev[i])
        
        qrout.apply(CNOT, a_rev[n-1], cout[0])
        
        for i in range(n-1, 0, -1):
            qrout.apply(_uma(), a_rev[i-1], b_rev[i], a_rev[i])
        qrout.apply(_uma(), cin[0], b_rev[0], a_rev[0])
    else:
        # modulo Cuccaro logic
        qrout.apply(_maj(), cin[0], b_rev[0], a_rev[0])
        for i in range(1, n):
            qrout.apply(_maj(), a_rev[i-1], b_rev[i], a_rev[i])
            
        for i in range(n-1, 0, -1):
            qrout.apply(_uma(), a_rev[i-1], b_rev[i], a_rev[i])
        qrout.apply(_uma(), cin[0], b_rev[0], a_rev[0])
    
    return qrout


# --- TAKAHASHI ADDER ---

@build_gate("TKK_ADD", [int, int, bool], arity=lambda al, bl, ov: al + bl + (1 if ov else 0))
def tkk_adder_int(a_len: int, b_len: int, overflow_qubit: bool = False):
    """
    Takahashi-Tani-Kunihiro ripple-carry adder.
    Performs |a>|b> -> |a>|a+b>.
    """
    qrout = QRoutine()
    a_orig = qrout.new_wires(a_len)
    b_orig = qrout.new_wires(b_len)
    
    n = max(a_len, b_len)
    
    a_rev = list(reversed(a_orig))
    b_rev = list(reversed(b_orig))
    
    # Pad with virtual zeros (ancillae) to match max length
    if a_len < n:
        a_pad = qrout.new_wires(n - a_len)
        qrout.set_ancillae(a_pad)
        a_rev += list(a_pad)
    if b_len < n:
        b_pad = qrout.new_wires(n - b_len)
        qrout.set_ancillae(b_pad)
        b_rev += list(b_pad)
        
    c_reg = qrout.new_wires(1)
    if not overflow_qubit:
        qrout.set_ancillae(c_reg)
    
    
    # First layer of CNOTs
    for i in range(1, n):
        qrout.apply(CNOT, a_rev[i], b_rev[i])
    
    # Final CNOT to carry register only if n > 1
    if n > 1:
        qrout.apply(CNOT, a_rev[n-1], c_reg[0])
        
    # Second layer of CNOTs
    for i in range(n - 1, 1, -1):
        qrout.apply(CNOT, a_rev[i-1], a_rev[i])
        
    # First layer of CCNOTs (Carry propagation)
    a_ext = a_rev + list(c_reg)
    for i in range(n):
        qrout.apply(CCNOT, a_rev[i], b_rev[i], a_ext[i+1])
        
    # Third layer of CNOTs and second layer of CCNOTs 
    for i in range(n - 1, 0, -1):
        qrout.apply(CNOT, a_rev[i], b_rev[i])
        qrout.apply(CCNOT, a_rev[i-1], b_rev[i-1], a_rev[i])
        
    # Fourth layer of CNOTs
    for i in range(1, n - 1):
        qrout.apply(CNOT, a_rev[i], a_rev[i+1])
        
    # Final layer of CNOTs
    for i in range(n):
        qrout.apply(CNOT, a_rev[i], b_rev[i])

    return qrout


# --- QFT ADDER ---

@build_gate("QFT", [int], arity=lambda n: n)
def _qft(n: int):
    """Quantum Fourier Transform for n qubits (Big-Endian)."""
    qrout = QRoutine()
    qbits = qrout.new_wires(n)
    for i in range(n):
        qrout.apply(H, qbits[i])
        for j in range(i + 1, n):
            # Controlled phase rotation: 2*pi / 2^(j-i+1)
            angle = 2 * math.pi / (2**(j - i + 1))
            qrout.apply(PH(angle).ctrl(), qbits[j], qbits[i])

    # Final swaps to match standard QFT ordering
    for i in range(n // 2):
        qrout.apply(SWAP, qbits[i], qbits[n - i - 1])
    return qrout


def _iqft(n: int):
    """Inverse Quantum Fourier Transform for n qubits."""
    return _qft(n).dag()

@build_gate("QFT_ADD", [int, int, bool], arity=lambda al, bl, ov: al + bl + (1 if ov else 0))
def qft_adder_int(a_len: int, b_len: int, overflow_qubit: bool = False):
    """
    QFT-based integer adder.
    Performs |a>|b> -> |a>|a+b> (mod 2^b_len or with overflow).
    """
    qrout = QRoutine()

    # Allocate interface wires first (a, b, then overflow)
    a_orig = qrout.new_wires(a_len)
    b_orig = qrout.new_wires(b_len)
    ov_orig = qrout.new_wires(1) if overflow_qubit else []

    n = max(a_len, b_len)
    target_len = n + (1 if overflow_qubit else 0)

    # Pad a with virtual zeros if needed
    a_wires = list(a_orig)
    if a_len < n:
        a_pad = qrout.new_wires(n - a_len)
        qrout.set_ancillae(a_pad)
        a_wires = list(a_pad) + a_wires  # MSB padding

    # Pad b with zeros if needed (and handle overflow qubit)
    if overflow_qubit:
        b_wires = [ov_orig[0]] + list(b_orig)
    else:
        b_wires = list(b_orig)

    if len(b_wires) < target_len:
        b_pad = qrout.new_wires(target_len - len(b_wires))
        qrout.set_ancillae(b_pad)
        if overflow_qubit:
            # Padding goes between overflow bit and original b bits
            b_wires = [b_wires[0]] + list(b_pad) + b_wires[1:]
        else:
            b_wires = list(b_pad) + b_wires

    # Transform target register to Fourier basis
    qrout.apply(_qft(target_len), b_wires)

    # Add a to b using controlled phase rotations
    for i in range(n):
        for j in range(target_len):
            k = i + j - n + 2
            if k > 0:
                angle = 2 * math.pi / (2**k)
                qrout.apply(PH(angle).ctrl(), a_wires[i], b_wires[j])

    # Transform back to computational basis
    qrout.apply(_iqft(target_len), b_wires)

    return qrout
