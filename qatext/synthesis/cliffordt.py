from qat.lang.AQASM.gates import H, S, CNOT, T, X, Z, AbstractGate
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate

from qat.core.gate_set import GateSet
from qat.lang.linking.linker import Linker

QAND = AbstractGate("AND", [], arity=3)
QAND_DAG = AbstractGate("AND_DAG", [], arity=3)

def get_new_cliffordt_linker():
    return Linker(gate_set=GateSet(), keep=["H", "S", "CNOT", "T"])

@build_gate("X", [], arity=1)
def x():
    qfun = QRoutine()
    wire = qfun.new_wires(1)
    qfun.apply(H, wire)
    qfun.apply(S, wire)
    qfun.apply(S, wire)
    qfun.apply(H, wire)
    return qfun

@build_gate("Z", [], arity=1)
def z():
    qfun = QRoutine()
    wire = qfun.new_wires(1)
    qfun.apply(S, wire)
    qfun.apply(S, wire)
    return qfun

@build_gate("Y", [], arity=1)
def y():
    qfun = QRoutine()
    wire = qfun.new_wires(1)
    qfun.apply(X, wire)
    qfun.apply(Z, wire)
    return qfun

@build_gate("CCNOT", [], arity=1)
def ccnot1():
    return _toffoli1()

@build_gate("C-C-X", [], arity=1)
def ccx1():
    return _toffoli1()

@build_gate("AND", [], arity=1)
def qand1():
    return _and1()

# Impossible to get since classic operations are disallowed

# @build_gate("AND_DAG", [], arity=3)
# def qand_dag2():
#     qfun = QRoutine()
#     a = qfun.new_wires(1)
#     b = qfun.new_wires(1)
#     c = qfun.new_wires(1) # result
#     d = qfun.new_wires(1) # either additional qubit or the same one used by AND
#     cadd = qfun.calloc(1)
#     qfun.set_ancillae(d)

#     CNOT(c, d) # copy c to d. We want to reuse c, and discard d
#     #
#     H(d)
#     qfun.measure(c, cadd)
#     qfun.cc_apply(cadd, X, c)
#     qfun.cc_apply(cadd, S, b)
#     qfun.cc_apply(cadd, S, a)
#     qfun.cc_apply(cadd, CNOT, a, b)
#     qfun.cc_apply(cadd, S.dag(), b)
#     qfun.cc_apply(cadd, CNOT, a, b)

#     return qfun


@build_gate("C-C-X", [], arity=1)
def ccx2():
    return _and1()

def _toffoli1():
    qfun = QRoutine()
    a = qfun.new_wires(1)
    b = qfun.new_wires(1)
    c = qfun.new_wires(1)
    H(c)
    T(a)
    T(b)
    T(c)
    CNOT(b, a)
    CNOT(c, a)
    CNOT(a, c)
    T.dag()(b)
    CNOT(a, b)
    T.dag()(a)
    T.dag()(b)
    T.dag()(c)
    CNOT(c, b)
    CNOT(a, c)
    CNOT(b, a)
    H(c)
    return qfun


def _and1():
    qfun = QRoutine()
    a = qfun.new_wires(1)
    b = qfun.new_wires(1)
    c = qfun.new_wires(1)
    d = qfun.new_wires(1)
    qfun.set_ancillae(d)

    H(c)
    CNOT(b, d)
    CNOT(c, a)
    CNOT(c, b)
    CNOT(a, d)
    T.dag()(a)
    T.dag()(b)
    T(c)
    T(d)
    CNOT(a, d)
    CNOT(c, b)
    CNOT(c, a)
    CNOT(b, d)
    H(c)
    S(c)
    
    return qfun


# class X2Clifford(QRoutine):
#     def __init__(self):
#         super().__init__()
#         wire = self.new_wires(1)
#         self.apply(H, wire)
#         self.apply(S, wire)
#         self.apply(S, wire)
#         self.apply(H, wire)


# @build_gate("X", [], arity=1)
# def x2clifford2():
#     return X2Clifford()
#     qfun = QRoutine()
#     a = qfun.new_wires(1)
#     b = qfun.new_wires(1)
#     c = qfun.new_wires(1)
#     qfun.apply(H, a)
#     qfun.apply(T, a)
#     qfun.apply(T, b)
#     qfun.apply(T, c)
#     return qfun

# @build_gate("C-C-X", [], arity=3)
# def ccx2cliford():


# @build_gate("RY", [float], arity=1)
# def ry(angle: float):
#     qfun = QRoutine()
#     wires = qfun.new_wires(1)
#     for gate in (S, H, RZ(angle), H, S.dag()):
#         qfun.apply(gate, wires[0])
#     return qfun


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
