from qat.lang.AQASM.gates import X, Z
from qat.lang.AQASM.routines import QRoutine

def flip_one(n):
    routine = QRoutine()
    wires = routine.new_wires(n)

    routine.apply(Z.ctrl(n - 1), wires)

    return routine


def flip_zero(n):
    routine = QRoutine()
    wires = routine.new_wires(n)

    with routine.compute():
        for wire in wires:
            routine.apply(X, wire)

    routine.apply(flip_one(n), wires)
    routine.uncompute()

    return routine
