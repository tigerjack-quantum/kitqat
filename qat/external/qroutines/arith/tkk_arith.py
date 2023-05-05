# -*- coding: utf-8 -*-
"""Ripple carry adder example based on [TaTK10] Takahashi, Yasuhiro ; Tani,
Seiichiro ; Kunihiro, Noboru: Quantum addition circuits and unbounded fan-out.
In: Quantum Information & Computation Bd. 10 (2010), Nr. 9 & 10, S. 872–890.
— Citation Key: DBLP:journals/qic/TakahashiTK10

"""

from qat.lang.AQASM.gates import CCNOT, CNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine


@build_gate("MADD", [int])
def adder(rlen: int) -> QRoutine:
    # assuming same length for now
    qrout = QRoutine()
    a = qrout.new_wires(rlen)
    b = qrout.new_wires(rlen)
    c_reg = qrout.new_wires(1)
    a_new = a + c_reg

    # print("*1*")
    i = None
    for i in range(1, rlen):
        qrout.apply(CNOT, a[i], b[i])
    if i is not None:
        qrout.apply(CNOT, a[i], c_reg)

    # print("*2*")
    for i in range(rlen - 1, 1, -1):
        qrout.apply(CNOT, a[i - 1], a[i])

    # print("*3*")
    for i in range(0, rlen):
        qrout.apply(CCNOT, a[i], b[i], a_new[i + 1])

    # print("*4*")
    for i in range(rlen - 1, 0, -1):
        qrout.apply(CNOT, a[i], b[i])
        qrout.apply(CCNOT, a[i - 1], b[i - 1], a[i])

    # print("*5*")
    for i in range(1, rlen - 1):
        qrout.apply(CNOT, a[i], a[i + 1])

    # print("*6*")
    for i in range(0, rlen):
        qrout.apply(CNOT, a[i], b[i])

    return qrout
