import logging

import numpy as np
from qat.lang.AQASM import CNOT, RY, QRoutine, X
from qat.lang.AQASM.misc import build_gate

logger = logging.getLogger(__name__)


def _scs(n: int, k: int) -> QRoutine:
    qf = QRoutine()
    wires = qf.new_wires(n)
    # i = 1
    angle = 2 * np.arccos(1 / np.sqrt(n))
    # print(f"angle sqrt of 1/{n}")
    qf.apply(CNOT, wires[n - 2], wires[n - 1])
    qf.apply(RY(angle).ctrl(), wires[n - 1], wires[n - 2])
    qf.apply(CNOT, wires[n - 2], wires[n - 1])
    # others i
    for i in range(2, k + 1):
        # print(f"i {i}")
        angle = 2 * np.arccos(np.sqrt(i / n))
        # print(f"angle sqrt of {i}/{n}")
        qf.apply(CNOT, wires[n - i - 1], wires[n - 1])
        qf.apply(RY(angle).ctrl(2), n - 1, n - i, n - i - 1)
        qf.apply(CNOT, wires[n - i - 1], wires[n - 1])
    return qf


@build_gate("DICKE", [int, int])
def generate(n: int, k: int) -> QRoutine:
    qf = QRoutine()
    wires = qf.new_wires(n)
    if k <= 0 or n < k:
        return qf
    if k == n:
        for qb in wires:
            qf.apply(X, qb)
        return qf

    localk = k if k <= n / 2 else n - k
    for i in range(n - 1, n - localk - 1, -1):
        qf.apply(X, wires[i])
    for i in range(n, localk, -1):
        # print(f"i, localk -> {i}, {localk}")
        qf.apply(_scs(i, localk), wires[:i])
    # print("****")
    for i in range(localk, 1, -1):
        # print(f"i, i-1 -> {i}, {i-1}")
        qf.apply(_scs(i, i - 1), wires[:i])
    if localk != k:
        for qb in wires:
            qf.apply(X, qb)
    return qf
