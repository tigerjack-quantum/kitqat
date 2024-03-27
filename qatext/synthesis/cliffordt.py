from qat.core.gate_set import GateSet
from qat.lang.AQASM.gates import CCNOT, CNOT, AbstractGate, H, S, T, X, Z
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from qat.lang.linking.linker import Linker

QAND = AbstractGate("QAND", [], arity=3)
# QAND_DAG = AbstractGate("QAND_DAG", [], arity=3)
TOFFOLI = AbstractGate("TOFF", [int], arity=lambda n: n)


def get_new_cliffordt_linker():
    return Linker(gate_set=GateSet(), keep=["H", "S", "CNOT", "T"])


class X2CnotToffoli(QRoutine):
    """Converts C-X to CNOT and C-C-X to CCNOT"""

    def __init__(self):
        super().__init__()
        wire = self.new_wires(1)
        self.apply(H, wire)
        self.apply(S, wire)
        self.apply(S, wire)
        self.apply(H, wire)

    def ctrl(self, nbctrls=1):
        rout = QRoutine()
        if nbctrls == 1:
            wires = rout.new_wires(2)
            rout.apply(CNOT, wires)
        elif nbctrls == 2:
            wires = rout.new_wires(3)
            rout.apply(CCNOT, wires)
        else:
            raise Exception("Cannot convert >2 ctrl X gates")
        return rout


@build_gate("X", [], arity=1)
def x1():
    return X2CnotToffoli()


class X2CnotQand(QRoutine):
    """Converts C-X to CNOT and C-C-X to QAND"""

    def __init__(self):
        super().__init__()
        wire = self.new_wires(1)
        self.apply(H, wire)
        self.apply(S, wire)
        self.apply(S, wire)
        self.apply(H, wire)

    def ctrl(self, nbctrls=1):
        rout = QRoutine()
        if nbctrls == 1:
            wires = rout.new_wires(2)
            rout.apply(CNOT, wires)
        elif nbctrls == 2:
            wires = rout.new_wires(3)
            rout.apply(QAND(), wires)
        else:
            raise Exception("Cannot convert >2 ctrl X gates")
        return rout


@build_gate("X", [], arity=1)
def x2():
    return X2CnotQand()


# @build_gate("X", [], arity=1)
# def x():
#     qfun = QRoutine()
#     wire = qfun.new_wires(1)
#     qfun.apply(H, wire)
#     qfun.apply(S, wire)
#     qfun.apply(S, wire)
#     qfun.apply(H, wire)
#     return qfun


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


@build_gate("CSIGN", [], arity=2)
def csign():
    return _cz()


# There's no C-Z actually, it is automatically converted to CSIGN
# @build_gate("C-Z", [], arity=2)
# def cz():
#     return _cz()


def _cz():
    qfun = QRoutine()
    wires = qfun.new_wires(2)
    H(wires[1])
    CNOT(wires)
    H(wires[1])
    return qfun


@build_gate("CCNOT", [], arity=1)
def ccnot1():
    return _toffoli3()


@build_gate("QAND", [], arity=1)
def qand1():
    return _qand1()


# Impossible to use since classic operations are disallowed
#
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


# Impossible, a C-C-U gate is simply obtained, by default, by decomposing U and
# applying 2 controls to all the gates of the decomposition

# @build_gate("C-C-X", [], arity=1)
# def ccx2():
#     return _qand1()


def _toffoli3():
    """From Amy et al. 2012"""
    qfun = QRoutine()
    a = qfun.new_wires(1)
    b = qfun.new_wires(1)
    c = qfun.new_wires(1)
    H(c)
    T.dag()(a)
    T(b)
    T(c)

    CNOT(a, b)
    CNOT(c, a)
    CNOT(b, c)
    T.dag()(a)
    CNOT(b, a)

    T.dag()(a)
    T.dag()(b)
    T(c)

    CNOT(c, a)
    CNOT(b, c)
    S(a)
    CNOT(a, b)
    H(c)
    return qfun


def _qand1():
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
    # T.dag is equivalent to SSST
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


# @build_gate("RY", [float], arity=1)
# def ry(angle: float):
#     qfun = QRoutine()
#     wires = qfun.new_wires(1)
#     for gate in (S, H, RZ(angle), H, S.dag()):
#         qfun.apply(gate, wires[0])
#     return qfun


# @build_gate("CRY", [], arity=2)
# def mcry():
#     qfun = QRoutine()
#     wires = qfun.new_wires(2)
#     qfun.apply(H, wires[0])
#     qfun.apply(T, wires[1])
#     return qfun
