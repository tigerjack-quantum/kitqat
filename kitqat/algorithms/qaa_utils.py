__authors__ = [
    "Simone Perriello <sperriello@proton.me>",
    "Alessandro Finazzi <alessandro2.finazzi@mail.polimi.it>",
]

import math

from kitqat.qroutines.rotation.flip_basis import flip_one
from qat.lang.AQASM.gates import X
from qat.lang.AQASM.routines import QRoutine


def precise_grover_iterations(N, M=1):
    theta = math.asin(math.sqrt(M / N))
    T_real = (math.pi / (4 * theta)) - 0.5

    candidates = [math.floor(T_real), math.ceil(T_real)]

    def success_prob(T):
        return math.sin((2 * T + 1) * theta)**2

    return max(candidates, key=success_prob)


def oracle(solution):
    routine = QRoutine()
    n = len(solution)
    wires = routine.new_wires(n)

    with routine.compute():
        # reversed for big-endianness
        for i in reversed(range(n)):
            if solution[i] == '0':
                routine.apply(X, wires[i])
    routine.apply(flip_one(n), wires)
    routine.uncompute()

    return routine
