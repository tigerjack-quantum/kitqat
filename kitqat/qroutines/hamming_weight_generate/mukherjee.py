# https://ieeexplore.ieee.org/ielx7/8924785/8943246/09275336.pdf
import logging

import numpy as np
from qat.lang.AQASM import CNOT, RY, QRoutine, X

# also called t1
def _u0(theta: float):
    """Implementation of U_0 gate."""
    qf = QRoutine()
    alpha2 = (np.pi - theta) / 2
    qf.apply(RY(-alpha2), 0)
    qf.apply(CNOT, 1, 0)
    qf.apply(RY(alpha2), 0)
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
        qf.apply(_scs(i, localk), wires[:i])
    for i in range(localk, 1, -1):
        qf.apply(_scs(i, i - 1), wires[:i])

    if localk != k:
        for qb in wires:
            qf.apply(X, qb)
    # global minangle, maxangle
    # print("*" * 40)
    # print(f"minangle = {minangle_val}")
    # print(f"maxangle = {maxangle_val}")
    return qf
