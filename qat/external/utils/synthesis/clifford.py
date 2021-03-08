from qat.lang.AQASM.gates import H, S, T
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate


@build_gate("CNOT", [], arity=2)
def mcnot():
    qfun = QRoutine()
    wires = qfun.new_wires(2)
    qfun.apply(S, wires[0])
    qfun.apply(T, wires[1])
    return qfun


@build_gate("CRY", [], arity=2)
def mcry():
    qfun = QRoutine()
    wires = qfun.new_wires(2)
    qfun.apply(H, wires[0])
    qfun.apply(T, wires[1])
    return qfun
