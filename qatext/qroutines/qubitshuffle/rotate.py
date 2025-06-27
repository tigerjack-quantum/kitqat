from qat.lang.AQASM.gates import SWAP, I
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.gates import AbstractGate
from qatext.qroutines.qubitshuffle.reverse import reverse

rotate = AbstractGate("ROT_D", [int, int], arity=lambda n, _: n)
rotate_reg = AbstractGate("ROT_REG_D", [int, int], arity=lambda n, _: n)

# Reversal alg., check
# https://www.geeksforgeeks.org/program-for-array-rotation-continued-reversal-algorithm/


# @build_gate('SHIFT', [int, int], lambda _, y: y)
# def shift_qreg(n_shifts, n_bits):
#     """Performs a cyclic left shift using only swaps (in-place)."""
#     qf = QRoutine()
#     n_shifts = n_shifts % n_bits  # Ensure the shift is within range
#     qreg = qf.new_wires(n_bits)
#     for _ in range(n_shifts):
#         for i in range(n_bits - 1):
#             qf.apply(SWAP, qreg[i], qreg[i + 1])
#     return qf


@build_gate('SWAP_QREG', [int], lambda x: x * 2)
def swap_qreg_cells(n_cell_size):
    """Swaps the matching qubits of two quantum registers having the same size"""
    qf = QRoutine()
    qreg1 = qf.new_wires(n_cell_size)
    qreg2 = qf.new_wires(n_cell_size)
    for cell_bit in range(n_cell_size):
        qf.apply(SWAP, qreg1[cell_bit], qreg2[cell_bit])
    return qf



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

@build_gate("ROT_REG_D", [int, int, int], arity=lambda n, n2, _: n * n2)
def reg_reversal(nregs: int,  qreg_size: int, d: int):
    """Rotate a set of `nregs` register by `d` positions. If d is >0, then it's
 a left rotation; if it's < 0, it's a right rotation. All the registers must be
 of the same size.

    """

    qrout = QRoutine()
    wires = qrout.new_wires(nregs * qreg_size)
    d2 = d * qreg_size

    qrout2 = reversal(len(wires), d2)
    qrout.apply(qrout2, wires)

    return qrout
