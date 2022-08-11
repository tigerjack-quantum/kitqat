from qat.lang.AQASM.gates import SWAP
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.gates import AbstractGate

lrot = AbstractGate("LROT", [int], arity=lambda n: n)


@build_gate("LROT", [int], arity=lambda n: n)
def left_rotate(nqubits: int) -> QRoutine:
    qrout = QRoutine()
    for i in range(nqubits - 1, 0, -1):
        qrout.apply(SWAP, i, i - 1)
    return qrout
