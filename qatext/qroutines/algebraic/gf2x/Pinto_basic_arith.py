from qat.lang.AQASM.gates import CNOT,CCNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

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

# Alias for subtraction (since addition and subtraction are identical in GF(2^m))
sub_n_bit = adder_n_bit