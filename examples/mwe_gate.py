from qat.lang.AQASM.gates import X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine


@build_gate("TEST_GATE", [])
def test_gate():
    qrout = QRoutine()
    qrout.apply(X, 1)
    return qrout
