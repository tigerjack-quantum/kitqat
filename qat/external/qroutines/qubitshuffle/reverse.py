from qat.lang.AQASM.gates import SWAP, I
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.gates import AbstractGate
from math import floor

reverse = AbstractGate("REVERSE", [int], arity=lambda n: n)


@build_gate("REVERSE", [int], arity=lambda n: n)
def reverse(nqubits: int) -> QRoutine:
    mid = int(floor(nqubits / 2))
    qrout = QRoutine()
    if mid <= 0:
        qrout.apply(I, 0)
        return qrout
    for i in range(mid):
        qrout.apply(SWAP, i, nqubits - i - 1)
    return qrout
