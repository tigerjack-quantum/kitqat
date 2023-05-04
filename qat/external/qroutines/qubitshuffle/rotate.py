from qat.lang.AQASM.gates import SWAP, I
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.gates import AbstractGate
from qat.external.qroutines.qubitshuffle.reverse import reverse

lrot = AbstractGate("LROT", [int], arity=lambda n: n)
rotate = AbstractGate("ROT_D", [int, int], arity=lambda n, _: n)

# Reversal alg., check
# https://www.geeksforgeeks.org/program-for-array-rotation-continued-reversal-algorithm/

@build_gate("ROT_D", [int, int], arity=lambda n, _: n)
def reversal(nqubits: int, d: int):
    """Totate a set of nqbubits by d position to the left"""
    qrout = QRoutine()
    d = d % nqubits
    wires = qrout.new_wires(nqubits)
    if d == 0 or d == nqubits:
        qrout.apply(I, wires[0])
        return qrout
    qrout.apply(reverse(nqubits), wires)
    qrout.apply(reverse(d), wires[nqubits-d:])
    qrout.apply(reverse(nqubits-d), wires[:nqubits-d])
    return qrout


# @build_gate("LROT", [int, int], arity=lambda n, _: n)
# def rotate(nqubits: int, nrotations: int) -> QRoutine:
#     """Totate for single qubits. If > 0, left rotate, """
#     qrout = QRoutine()
#     for i in range(nqubits - 1, 0, -1):
#         qrout.apply(SWAP, i, i - 1)
#     return qrout


# @build_gate("LROT_REG", [int, int], arity=lambda n1, n2: n1 * n2)
# def left_rotate(nregs: int, regsize: int) -> QRoutine:
#     """Left rotate for nregs register, each composed of regsize qubits"""
#     qrout = QRoutine()

#     for i in range(nregs - 1, 0, -1):
#         for j in range(regsize - 1, 0, -1):
#             qrout.apply(SWAP, i*regsize + j, (i*regsize + j) - 1)
#     return qrout
