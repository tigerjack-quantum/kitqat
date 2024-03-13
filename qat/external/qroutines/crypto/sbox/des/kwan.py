"""
Define the DES Sbox
"""

import logging

from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.qbool import QBoolArray
from qat.lang.AQASM.routines import QRoutine

LOGGER = logging.getLogger(__name__)


def _helper(expr, output):
    expr.evaluate(output=output)
    return output


@build_gate("DES_S1", [], lambda: 10)
def s1() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = qr.new_wires(4, QBoolArray)
    # x = qr.new_wires(63, QBoolArray)
    # ancs = qr.new_wires(10)
    tmps = qr.new_wires(59, QBoolArray)
    qr.set_ancillae(tmps)

    x0 = _helper(~a[3], tmps[0])
    x1 = _helper(~a[0], tmps[1])
    x2 = _helper(a[3] ^ a[2], tmps[2])
    x3 = _helper(x2 ^ x1, tmps[3])
    x4 = _helper(a[2] | x1, tmps[4])
    x5 = _helper(x4 & x0, tmps[5])
    x6 = _helper(a[5] | x5, tmps[6])
    x7 = _helper(x3 ^ x6, output=tmps[7])
    x8 = _helper(x0 | x1, output=tmps[8])
    x9 = _helper(a[5] & x8, output=tmps[9])
    x10 = _helper(x6 ^ x9, output=tmps[10])
    x11 = _helper(a[1] | x10, output=tmps[11])
    x12 = _helper(x7 ^ x11, output=tmps[12])
    x13 = _helper(x8 ^ x12, output=tmps[13])
    x14 = _helper(a[5] | x13, output=tmps[14])
    x15 = _helper(x0 ^ x14, output=tmps[15])
    x16 = _helper(~x13, output=tmps[16])
    x17 = _helper(x16 & x2, output=tmps[17])
    x18 = _helper(a[1] | x17, output=tmps[18])
    x19 = _helper(x15 ^ x18, output=tmps[19])
    x20 = _helper(a[4] | x19, output=tmps[20])
    _ = _helper(x12 ^ x20, output=outs[3])

    x22 = _helper(a[2] | x3, tmps[21])
    x23 = _helper(~x22, tmps[22])
    x24 = _helper(a[5] | x23, tmps[23])
    x25 = _helper(x5 ^ x24, tmps[24])
    x26 = _helper(x0 & x7, tmps[25])
    x27 = _helper(a[1] | x26, tmps[26])
    x28 = _helper(x25 ^ x27, tmps[27])
    x29 = _helper(x0 | x7, tmps[28])
    x30 = _helper(x29 ^ x5, tmps[29])
    x31 = _helper(x4 & x13, tmps[30])
    x32 = _helper(x31 ^ x7, tmps[31])
    x33 = _helper(a[1] & x32, tmps[32])
    x34 = _helper(x30 ^ x33, tmps[33])
    x35 = _helper(a[4] | x34, tmps[34])
    _ = _helper(x28 ^ x35, outs[0])

    x37 = _helper(a[2] & x9, tmps[35])
    x38 = _helper(x37 | x3, tmps[36])
    x39 = _helper(a[2] & x32, tmps[37])
    x40 = _helper(x39 ^ x24, tmps[38])
    x41 = _helper(a[1] | x40, tmps[39])
    x42 = _helper(x38 ^ x41, tmps[40])
    x43 = _helper(a[2] | x25, tmps[41])
    x44 = _helper(x43 ^ x13, tmps[42])
    x45 = _helper(a[0] | x7, tmps[43])
    x46 = _helper(x45 ^ x19, tmps[44])
    x47 = _helper(a[1] | x46, tmps[45])
    x48 = _helper(x44 ^ x47, tmps[46])
    x49 = _helper(a[4] & x48, tmps[47])
    _ = _helper(x42 ^ x49, outs[1])

    x51 = _helper(x7 ^ x39, tmps[48])
    x52 = _helper(a[2] ^ x10, tmps[49])
    x53 = _helper(x52 & x4, tmps[50])
    x54 = _helper(a[1] | x53, tmps[51])
    x55 = _helper(x51 ^ x54, tmps[52])
    x56 = _helper(a[5] | x3, tmps[53])
    x57 = _helper(x56 ^ x37, tmps[54])
    x58 = _helper(x12 & x55, tmps[55])
    x59 = _helper(a[1] & x58, tmps[56])
    x60 = _helper(x57 ^ x59, tmps[57])
    x61 = _helper(a[4] & x60, tmps[58])
    _ = _helper(x55 ^ x61, outs[2])

    return qr


@build_gate("DES_S2", [], lambda: 10)
def s2() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = qr.new_wires(4, QBoolArray)
    # x = qr.new_wires(63, QBoolArray)
    # ancs = qr.new_wires(10)
    tmps = qr.new_wires(59, QBoolArray)
    qr.set_ancillae(tmps)
    pass


@build_gate("DES_S3", [], lambda: 10)
def s3() -> QRoutine:
    pass


@build_gate("DES_S4", [], lambda: 10)
def s4() -> QRoutine:
    pass


@build_gate("DES_S4", [], lambda: 10)
def s4() -> QRoutine:
    pass


@build_gate("DES_S5", [], lambda: 10)
def s5() -> QRoutine:
    pass


@build_gate("DES_S6", [], lambda: 10)
def s6() -> QRoutine:
    pass


@build_gate("DES_S7", [], lambda: 10)
def s7() -> QRoutine:
    pass


@build_gate("DES_S8", [], lambda: 10)
def s8() -> QRoutine:
    pass


sboxes = (s1, s2, s3, s4, s5, s6, s7, s8)

# @build_gate("DES_S1", [], lambda : 10 )
# def s1__helper() -> QRoutine:
#     qr = QRoutine()
#     a = qr.new_wires(6, QBoolArray)
#     outs = qr.new_wires(4, QBoolArray)
#     # x = qr.new_wires(63, QBoolArray)
#     # ancs = qr.new_wires(10)
#     tmps = qr.new_wires(4, QBoolArray)

#     x0 = ~a[3]
#     x1 = ~a[0]
#     x2 = a[3] ^ a[2]
#     x3 = x2 ^ x1
#     x4 = a[2] | x1
#     x5 = x4 & x0
#     x6 = a[5] | x5
#     x7 = x3 ^ x6
#     # x7.evaluate(output=outs[3])
#     x8 = x0 | x1
#     x9 = a[5] & x8
#     x10 = x6 ^ x9
#     x11 = a[1] | x10
#     x12 = x7 ^ x11
#     x13 = x8 ^ x12
#     x14 = a[5] | x13
#     x15 = x0 ^ x14
#     x16 = ~x13
#     x17 = x16 & x2
#     x18 = a[1] | x17
#     x19 = x15 ^ x18
#     x20 = a[4] | x19
#     x20.evaluate(output=tmps[0])
#     x20 = tmps[0]
#     x12.evaluate(output=tmps[1])
#     x12 = tmps[1]
#     x21 = x12 ^ x20
#     # *out3 ^= x21
#     x21.evaluate(output=outs[3])

#     x22 = a[2] | x3
#     x23 = ~x22
#     x24 = a[5] | x23
#     x25 = x5 ^ x24
#     x26 = x0 & x7
#     x27 = a[1] | x26
#     x28 = x25 ^ x27
#     x29 = x0 | x7
#     x30 = x29 ^ x5
#     x31 = x4 & x13
#     x32 = x31 ^ x7
#     x33 = a[1] & x32
#     x34 = x30 ^ x33
#     x35 = a[4] | x34
#     x36 = x28 ^ x35
#     # *out0 ^= x36
#     x36.evaluate(output=outs[0])

#     x37 = a[2] & x9
#     x38 = x37 | x3
#     x39 = a[2] & x32
#     x40 = x39 ^ x24
#     x41 = a[1] | x40
#     x42 = x38 ^ x41
#     x43 = a[2] | x25
#     x44 = x43 ^ x13
#     x45 = a[0] | x7
#     x46 = x45 ^ x19
#     x47 = a[1] | x46
#     x48 = x44 ^ x47
#     x49 = a[4] & x48
#     x50 = x42 ^ x49
#     # *out1 ^= x50
#     x50.evaluate(output=outs[1])

#     # x51 = x7 ^ x39
#     # x52 = a[2] ^ x10
#     # x53 = x52 & x4
#     # x54 = a[1] | x53
#     # x55 = x51 ^ x54
#     # x56 = a[5] | x3
#     # x57 = x56 ^ x37
#     # x58 = x12 & x55
#     # x59 = a[1] & x58
#     # x60 = x57 ^ x59
#     # x61 = a[4] & x60
#     # x62 = x55 ^ x61
#     # # *out2 ^= x62
#     # x62.evaluate(output=outs[2])

#     return qr

# @build_gate("DES_S1", [], lambda : 10 )
# def s1_b() -> QRoutine:
#     qr = QRoutine()
#     a = qr.new_wires(6, QBoolArray)
#     outs = qr.new_wires(4, QBoolArray)
#     # x = qr.new_wires(63, QBoolArray)
#     # ancs = qr.new_wires(10)
#     tmps = qr.new_wires(21, QBoolArray)
#     qr.set_ancillae(tmps)

#     x0 = ~a[3]
#     x0.evaluate(output=tmps[0])
#     x0 = tmps[0]
#     x1 = ~a[0]
#     x1.evaluate(output=tmps[1])
#     x1 = tmps[1]
#     x2 = a[3] ^ a[2]
#     x2.evaluate(output=tmps[2])
#     x2 = tmps[2]
#     x3 = x2 ^ x1
#     x3.evaluate(output=tmps[3])
#     x3 = tmps[3]
#     x4 = a[2] | x1
#     x4.evaluate(output=tmps[4])
#     x4 = tmps[4]
#     x5 = x4 & x0
#     x5.evaluate(output=tmps[5])
#     x5 = tmps[5]
#     x6 = a[5] | x5
#     x6.evaluate(output=tmps[6])
#     x6 = tmps[6]
#     x7 = x3 ^ x6
#     x7.evaluate(output=tmps[7])
#     x7 = tmps[7]
#     x8 = x0 | x1
#     x8.evaluate(output=tmps[8])
#     x8 = tmps[8]
#     x9 = a[5] & x8
#     x9.evaluate(output=tmps[9])
#     x9 = tmps[9]
#     x10 = x6 ^ x9
#     x10.evaluate(output=tmps[10])
#     x10 = tmps[10]
#     x11 = a[1] | x10
#     x11.evaluate(output=tmps[11])
#     x11 = tmps[11]

#     x12 = x7 ^ x11
#     x12.evaluate(output=tmps[12])
#     x12 = tmps[12]

#     x13 = x8 ^ x12
#     x13.evaluate(output=tmps[13])
#     x13 = tmps[13]

#     x14 = a[5] | x13
#     x14.evaluate(output=tmps[14])
#     x14 = tmps[14]

#     x15 = x0 ^ x14
#     x15.evaluate(output=tmps[15])
#     x15 = tmps[15]

#     x16 = ~x13
#     x15.evaluate(output=tmps[15])
#     x15 = tmps[15]

#     x17 = x16 & x2
#     x17.evaluate(output=tmps[17])
#     x17 = tmps[17]

#     x18 = a[1] | x17
#     x18.evaluate(output=tmps[18])
#     x18 = tmps[18]

#     x19 = x15 ^ x18
#     x19.evaluate(output=tmps[19])
#     x19 = tmps[19]

#     x20 = a[4] | x19
#     x20.evaluate(output=tmps[20])
#     x20 = tmps[20]


#     x21 = x12 ^ x20
#     x21.evaluate(output=outs[3])
#     x21 = outs[3]
#     # *out3 ^= x21
#     # x21.evaluate(output=outs[3])

#     return qr
