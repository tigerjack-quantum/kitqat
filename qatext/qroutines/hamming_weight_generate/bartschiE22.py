"""bartschiShortdepthCircuitsDicke2022."""

import logging

import numpy as np
from qat.lang.AQASM.gates import CNOT, RY, X
from qat.lang.AQASM.routines import QRoutine
from qat.lang.AQASM.misc import build_gate
from math import comb

logger = logging.getLogger(__name__)


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

    # for i in range(n, localk, -1):
    #     qf.apply(_scs(i, localk), wires[:i])
    # for i in range(localk, 1, -1):
    #     qf.apply(_scs(i, i - 1), wires[:i])

    if localk != k:
        for qb in wires:
            qf.apply(X, qb)
    return qf


@build_gate("_WDB", [int, int, int])
def weight_distribute(n: int, k: int, m: int) -> QRoutine:
    pass


@build_gate("_ONEHOT", [int, int])
def onehot_encoding(nz: int, l: int) -> QRoutine:
    """nz stands for n_0, since it's not the original n but the number of
    qubits of this subfunction."""
    qf = QRoutine()
    print("onehot")
    wires = qf.new_wires(nz)
    for i in range(1, l):
        print(f"{wires[i-1]}, {wires[i]}")
        qf.apply(CNOT, wires[i], wires[i - 1])

    return qf


# @build_gate("_CADD", [int, int, int])
def controlled_additions(
    n: int,
    m: int,
    l: int,
):
    xs = []
    ss = []
    for i in range(0, l):
        xs.append(comb(m, i) * comb(n - m, l - i))
        term = 0 if i == 0 else ss[i - 1]
        ss.append(term + xs[i])
    print(xs)
    print(ss)
