from qat.lang.AQASM.gates import SWAP, I
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.gates import AbstractGate
from qat.external.qroutines.qubitshuffle.reverse import reverse

rotate = AbstractGate("ROT_D", [int, int], arity=lambda n, _: n)

# Reversal alg., check
# https://www.geeksforgeeks.org/program-for-array-rotation-continued-reversal-algorithm/

@build_gate("ROT_D", [int, int], arity=lambda n, _: n)
def reversal(nqubits: int, d: int):
    """Rotate a set of nqbubits by d position. If d is >0, then it's a left
    rotation; if it's < 0, it's a right rotation."""
    qrout = QRoutine()
    wires = qrout.new_wires(nqubits)
    d1 = abs(d) % nqubits
    if d1 == 0 or d1 == nqubits:
        qrout.apply(I, wires[0])
        return qrout
    qrout.apply(reverse(nqubits), wires)
    if d > 0:
        qrout.apply(reverse(d1), wires[nqubits-d1:])
        qrout.apply(reverse(nqubits-d1), wires[:nqubits-d1])
    else:
        qrout.apply(reverse(d1), wires[:d1])
        qrout.apply(reverse(nqubits-d1), wires[d1:])
    return qrout
