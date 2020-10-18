from qat.lang.AQASM import CNOT, AbstractGate, RY, QRoutine
from qat.lang.AQASM.misc import build_gate

MCRY = AbstractGate("MCRY", [float], arity=2)
MCCRY = AbstractGate("MCCRY", [float], arity=3)

# see arxiv:2007.01681, Fig.3
@build_gate("MCRY", [float], arity=2)
# @build_gate("C-RY", [float], arity=2)
def mcry_simple(angle):
    qfun = QRoutine()
    ctrl = qfun.new_wires(1)
    tgt =  qfun.new_wires(1)
    qfun.apply(CNOT, ctrl, tgt)
    qfun.apply(RY(-angle/2), tgt)
    qfun.apply(CNOT, ctrl, tgt)
    qfun.apply(RY(angle/2), tgt)
    return qfun

# see arxiv:1904.07358, Fig.3
@build_gate("MCCRY", [float], arity=2)
def mccry_simple(angle):
    qfun = QRoutine()
    ctrl = qfun.new_wires(2)
    tgt =  qfun.new_wires(1)
    qfun.apply(CNOT, ctrl[1], tgt)
    qfun.apply(RY(-angle/4), tgt)
    qfun.apply(CNOT, ctrl[0], tgt)
    qfun.apply(RY(angle/4), tgt)
    qfun.apply(CNOT, ctrl[1], tgt)
    qfun.apply(RY(-angle/4), tgt)
    qfun.apply(CNOT, ctrl[0], tgt)
    qfun.apply(RY(angle/4), tgt)
    return qfun
