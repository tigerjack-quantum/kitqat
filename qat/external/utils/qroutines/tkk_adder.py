# -*- coding: utf-8 -*-
"""Ripple carry adder example based on [TaTK10]  Takahashi, Yasuhiro ; Tani, Seiichiro ; Kunihiro, Noboru: Quantum addition circuits and unbounded fan-out. In: Quantum Information & Computation Bd. 10 (2010), Nr. 9 & 10, S. 872–890. — Citation Key: DBLP:journals/qic/TakahashiTK10
"""

from qat.lang.AQASM.gates import CCNOT, CNOT, X
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
    for i in range(1, rlen):
        # print(f"CNOT a{i} b{i}")
        qrout.apply(CNOT, a[i], b[i])
    try:
        qrout.apply(CNOT, a[i], c_reg)
        # print(f"CNOT a{i} c_reg")
    except:
        # simply, i is not assigned
        pass

    # print("*2*")
    for i in range(rlen - 1, 1, -1):
        # print(f"CNOT a{i-1} a{i}")
        qrout.apply(CNOT, a[i-1], a[i])

    # print("*3*")
    for i in range(0, rlen):
        # print(f"CCNOT a{i} b{i} a_new{i+1}")
        qrout.apply(CCNOT, a[i], b[i], a_new[i+1])

    # print("*4*")
    for i in range(rlen - 1, 0, -1):
        # print(f"CNOT a{i} b{i}")
        qrout.apply(CNOT, a[i], b[i])
        # print(f"CCNOT a{i-1} b{i-1} a{i}")
        qrout.apply(CCNOT, a[i-1], b[i-1], a[i])

    # print("*5*")
    for i in range(1, rlen - 1):
        # print(f"CNOT a{i} a{i+1}")
        qrout.apply(CNOT, a[i], a[i+1])

    # print("*6*")
    for i in range(0, rlen):
        # print(f"CNOT a{i} b{i}")
        qrout.apply(CNOT, a[i], b[i])

    return qrout
