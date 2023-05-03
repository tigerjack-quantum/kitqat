from qat.lang.AQASM.gates import H, RZ, S
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate


@build_gate("X", [], arity=1)
def x2clifford():
    qfun = QRoutine()
    wire = qfun.new_wires(1)
    qfun.apply(H, wire)
    qfun.apply(S, wire)
    qfun.apply(S, wire)
    qfun.apply(H, wire)
    return qfun


class X2Clifford(QRoutine):
    def __init__(self):
        super().__init__()
        wire = self.new_wires(1)
        self.apply(H, wire)
        self.apply(S, wire)
        self.apply(S, wire)
        self.apply(H, wire)


@build_gate("X", [], arity=1)
def x2clifford2():
    return X2Clifford()


@build_gate("RY", [float], arity=1)
def ry(angle: float):
    qfun = QRoutine()
    wires = qfun.new_wires(1)
    for gate in (S, H, RZ(angle), H, S.dag()):
        qfun.apply(gate, wires[0])
    return qfun


# @build_gate("CNOT", [], arity=2)
# def mcnot():
#     qfun = QRoutine()
#     wires = qfun.new_wires(2)
#     qfun.apply(S, wires[0])
#     qfun.apply(T, wires[1])
#     return qfun

# @build_gate("CRY", [], arity=2)
# def mcry():
#     qfun = QRoutine()
#     wires = qfun.new_wires(2)
#     qfun.apply(H, wires[0])
#     qfun.apply(T, wires[1])
#     return qfun
