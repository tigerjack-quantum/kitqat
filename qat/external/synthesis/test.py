from qat.lang.AQASM.gates import H, S, T, Z
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate

from qat.lang.AQASM import *
from qat.core.console import display


@build_gate("X", [], arity=1)
def x2clifford():
    qfun = QRoutine()
    wire = qfun.new_wires(1)
    qfun.apply(H, wire)
    qfun.apply(Z, wire)
    qfun.apply(H, wire)
    return qfun


class X2Clifford(QRoutine):
    def __init__(self):
        super().__init__()
        wire = self.new_wires(1)
        self.apply(H, wire)
        self.apply(Z, wire)
        self.apply(H, wire)


@build_gate("X", [], arity=1)
def x2clifford2():
    return X2Clifford()


# def main():
#     pr = Program()
#     qr = pr.qalloc(2)
#     pr.apply(X, qr[0])
#     pr.apply(X.ctrl(1), qr)
#     cr = pr.to_circ(link=[x2clifford], inline=True)
#     display(cr)
#     # display(cr, max_depth=2)


# if __name__ == '__main__':
#     main()
