"""
Define the DES Sbox
"""

import logging
from typing import Optional

from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.qbool import QBoolArray
from qat.lang.AQASM.routines import QRoutine

LOGGER = logging.getLogger(__name__)


def _helper(expr, qr: Optional[QRoutine] = None, output=None):
    if output is None:
        if qr is None:
            raise Exception("Either qr or output should be not None")
        output = qr.new_wires(1, QBoolArray)
        qr.set_ancillae(output)
        output = output[0]

    expr.evaluate(output=output)
    return output


@build_gate("DES_S1", [], lambda: 10)
def s1() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = qr.new_wires(4, QBoolArray)

    x0 = _helper(~a[3], qr)
    x1 = _helper(~a[0], qr)
    x2 = _helper(a[3] ^ a[2], qr)
    x3 = _helper(x2 ^ x1, qr)
    x4 = _helper(a[2] | x1, qr)
    x5 = _helper(x4 & x0, qr)
    x6 = _helper(a[5] | x5, qr)
    x7 = _helper(x3 ^ x6, qr)
    x8 = _helper(x0 | x1, qr)
    x9 = _helper(a[5] & x8, qr)
    x10 = _helper(x6 ^ x9, qr)
    x11 = _helper(a[1] | x10, qr)
    x12 = _helper(x7 ^ x11, qr)
    x13 = _helper(x8 ^ x12, qr)
    x14 = _helper(a[5] | x13, qr)
    x15 = _helper(x0 ^ x14, qr)
    x16 = _helper(~x13, qr)
    x17 = _helper(x16 & x2, qr)
    x18 = _helper(a[1] | x17, qr)
    x19 = _helper(x15 ^ x18, qr)
    x20 = _helper(a[4] | x19, qr)
    _ = _helper(x12 ^ x20, output=outs[3])

    x22 = _helper(a[2] | x3, qr)
    x23 = _helper(~x22, qr)
    x24 = _helper(a[5] | x23, qr)
    x25 = _helper(x5 ^ x24, qr)
    x26 = _helper(x0 & x7, qr)
    x27 = _helper(a[1] | x26, qr)
    x28 = _helper(x25 ^ x27, qr)
    x29 = _helper(x0 | x7, qr)
    x30 = _helper(x29 ^ x5, qr)
    x31 = _helper(x4 & x13, qr)
    x32 = _helper(x31 ^ x7, qr)
    x33 = _helper(a[1] & x32, qr)
    x34 = _helper(x30 ^ x33, qr)
    x35 = _helper(a[4] | x34, qr)
    _ = _helper(x28 ^ x35, output=outs[0])

    x37 = _helper(a[2] & x9, qr)
    x38 = _helper(x37 | x3, qr)
    x39 = _helper(a[2] & x32, qr)
    x40 = _helper(x39 ^ x24, qr)
    x41 = _helper(a[1] | x40, qr)
    x42 = _helper(x38 ^ x41, qr)
    x43 = _helper(a[2] | x25, qr)
    x44 = _helper(x43 ^ x13, qr)
    x45 = _helper(a[0] | x7, qr)
    x46 = _helper(x45 ^ x19, qr)
    x47 = _helper(a[1] | x46, qr)
    x48 = _helper(x44 ^ x47, qr)
    x49 = _helper(a[4] & x48, qr)
    _ = _helper(x42 ^ x49, output=outs[1])

    x51 = _helper(x7 ^ x39, qr)
    x52 = _helper(a[2] ^ x10, qr)
    x53 = _helper(x52 & x4, qr)
    x54 = _helper(a[1] | x53, qr)
    x55 = _helper(x51 ^ x54, qr)
    x56 = _helper(a[5] | x3, qr)
    x57 = _helper(x56 ^ x37, qr)
    x58 = _helper(x12 & x55, qr)
    x59 = _helper(a[1] & x58, qr)
    x60 = _helper(x57 ^ x59, qr)
    x61 = _helper(a[4] & x60, qr)
    _ = _helper(x55 ^ x61, output=outs[2])

    return qr


@build_gate("DES_S2", [], lambda: 10)
def s2() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = outs = qr.new_wires(4, QBoolArray)

    x0 = _helper(~a[4], qr)
    x1 = _helper(~a[0], qr)
    x2 = _helper(a[4] ^ a[5], qr)
    x3 = _helper(x2 ^ x1, qr)
    x4 = _helper(x3 ^ a[1], qr)
    x5 = _helper(a[5] | x0, qr)
    x6 = _helper(x5 | x1, qr)
    x7 = _helper(a[1] & x6, qr)
    x8 = _helper(a[5] ^ x7, qr)
    x9 = _helper(a[2] & x8, qr)
    x10 = _helper(x4 ^ x9, qr)
    x11 = _helper(a[1] & x8, qr)
    x12 = _helper(a[4] ^ x5, qr)
    x13 = _helper(a[2] | x12, qr)
    x14 = _helper(x11 ^ x13, qr)
    x15 = _helper(a[3] & x14, qr)
    x16 = _helper(x10 ^ x15, output=outs[1])

    x17 = _helper(a[4] | a[0], qr)
    x18 = _helper(a[5] | x17, qr)
    x19 = _helper(x12 ^ x18, qr)
    x20 = _helper(x19 ^ a[1], qr)
    x21 = _helper(a[5] | x3, qr)
    x22 = _helper(x21 & x16, qr)
    x23 = _helper(a[2] | x22, qr)
    x24 = _helper(x20 ^ x23, qr)
    x25 = _helper(a[5] | x1, qr)
    x26 = _helper(a[4] & x1, qr)
    x27 = _helper(a[1] | x26, qr)
    x28 = _helper(x25 ^ x27, qr)
    x29 = _helper(x2 ^ x26, qr)
    x30 = _helper(x1 ^ x18, qr)
    x31 = _helper(a[1] & x30, qr)
    x32 = _helper(x29 ^ x31, qr)
    x33 = _helper(a[2] & x32, qr)
    x34 = _helper(x28 ^ x33, qr)
    x35 = _helper(a[3] | x34, qr)
    _ = _helper(x24 ^ x35, output=outs[2])

    x37 = _helper(x20 & x31, qr)
    x38 = _helper(x37 ^ x4, qr)
    x39 = _helper(a[0] | x14, qr)
    x40 = _helper(x39 ^ x12, qr)
    x41 = _helper(a[2] | x40, qr)
    x42 = _helper(x38 ^ x41, qr)
    x43 = _helper(x27 | x40, qr)
    x44 = _helper(a[3] & x43, qr)
    _ = _helper(x42 ^ x44, output=outs[0])
    # out0 ^= _helper(x45, tmps[])

    x46 = _helper(x18 & x20, qr)
    x47 = _helper(x46 ^ x25, qr)
    x48 = _helper(a[1] & x32, qr)
    x49 = _helper(x48 ^ x20, qr)
    x50 = _helper(a[2] & x49, qr)
    x51 = _helper(x47 ^ x50, qr)
    x52 = _helper(x17 & x27, qr)
    x53 = _helper(x52 & x49, qr)
    x54 = _helper(a[3] | x53, qr)
    _ = _helper(x51 ^ x54, output=outs[3])
    # out3 ^= _helper(x55, tmps[])

    return qr


@build_gate("DES_S3", [], lambda: 10)
def s3() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = outs = qr.new_wires(4, QBoolArray)

    x0 = _helper(~a[4], qr)
    x1 = _helper(~a[5], qr)
    x2 = _helper(a[4] & a[2], qr)
    x3 = _helper(x2 ^ a[5], qr)
    x4 = _helper(a[3] & x0, qr)
    x5 = _helper(x3 ^ x4, qr)
    x6 = _helper(x5 ^ a[1], qr)
    x7 = _helper(a[2] & x0, qr)
    x8 = _helper(a[4] ^ x1, qr)
    x9 = _helper(a[3] | x8, qr)
    x10 = _helper(x7 ^ x9, qr)
    x11 = _helper(x6 & x10, qr)
    x12 = _helper(a[4] ^ x10, qr)
    x13 = _helper(x12 | x6, qr)
    x14 = _helper(a[3] & x13, qr)
    x15 = _helper(x11 ^ x14, qr)
    x16 = _helper(a[1] & x15, qr)
    x17 = _helper(x10 ^ x16, qr)
    x18 = _helper(a[0] & x17, qr)
    _ = _helper(x6 ^ x18, output=outs[3])
    # *out3 ^= _helper(x19, tmps[])

    x20 = _helper(a[2] ^ a[3], qr)
    x21 = _helper(x20 ^ x8, qr)
    x22 = _helper(x1 | x3, qr)
    x23 = _helper(x22 ^ x7, qr)
    x24 = _helper(a[1] | x23, qr)
    x25 = _helper(x21 ^ x24, qr)
    x26 = _helper(a[5] ^ x22, qr)
    x27 = _helper(x26 | a[3], qr)
    x28 = _helper(a[2] ^ x14, qr)
    x29 = _helper(x28 | x4, qr)
    x30 = _helper(a[1] | x29, qr)
    x31 = _helper(x27 ^ x30, qr)
    x32 = _helper(a[0] | x31, qr)
    x33 = _helper(x25 ^ x32, output=outs[0])
    # *out0 ^= _helper(x33, tmps[])

    x34 = _helper(a[2] ^ x8, qr)
    x35 = _helper(x34 | x4, qr)
    x36 = _helper(x3 | x28, qr)
    x37 = _helper(x36 ^ a[3], qr)
    x38 = _helper(a[1] | x37, qr)
    x39 = _helper(x35 ^ x38, qr)
    x40 = _helper(a[5] & x10, qr)
    x41 = _helper(x40 | x5, qr)
    x42 = _helper(x33 ^ x37, qr)
    x43 = _helper(x42 ^ x40, qr)
    x44 = _helper(a[1] & x43, qr)
    x45 = _helper(x41 ^ x44, qr)
    x46 = _helper(a[0] | x45, qr)
    _ = _helper(x39 ^ x46, output=outs[2])
    # *out2 ^= _helper(x47, tmps[])

    x48 = _helper(x1 | x37, qr)
    x49 = _helper(x48 ^ x12, qr)
    x50 = _helper(x26 ^ x27, qr)
    x51 = _helper(a[1] | x50, qr)
    x52 = _helper(x49 ^ x51, qr)
    x53 = _helper(x11 & x22, qr)
    x54 = _helper(x53 & x51, qr)
    x55 = _helper(a[0] | x54, qr)
    _ = _helper(x52 ^ x55, output=outs[1])
    # *out1 ^= _helper(x56, tmps[])

    return qr


@build_gate("DES_S4", [], lambda: 10)
def s4() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = qr.new_wires(4, QBoolArray)
    # tmps = qr.new_wires(38, QBoolArray)
    # qr.set_ancillae(tmps)

    x0 = _helper(~a[0], qr)
    x1 = _helper(~a[2], qr)
    x2 = _helper(a[0] | a[2], qr)
    x3 = _helper(a[4] & x2, qr)
    x4 = _helper(x0 ^ x3, qr)
    x5 = _helper(a[1] | a[2], qr)
    x6 = _helper(x4 ^ x5, qr)
    x7 = _helper(a[0] & a[4], qr)
    x8 = _helper(x7 ^ x2, qr)
    x9 = _helper(a[1] & x8, qr)
    x10 = _helper(a[4] ^ x9, qr)
    x11 = _helper(a[3] & x10, qr)
    x12 = _helper(x6 ^ x11, qr)
    x13 = _helper(x1 ^ x3, qr)
    x14 = _helper(a[1] & x13, qr)
    x15 = _helper(x8 ^ x14, qr)
    x16 = _helper(x4 & x13, qr)
    x17 = _helper(a[4] ^ x1, qr)
    x18 = _helper(a[1] | x17, qr)
    x19 = _helper(x16 ^ x18, qr)
    x20 = _helper(a[3] | x19, qr)
    x21 = _helper(x15 ^ x20, qr)
    x22 = _helper(a[5] & x21, qr)
    x23 = _helper(x12 ^ x22, output=outs[1])
    # *out1 ^= _helper(x23, tmps[])

    x24 = _helper(~x12, qr)
    x25 = _helper(a[5] | x21, qr)
    _ = _helper(x24 ^ x25, output=outs[0])
    # *out0 ^= _helper(x26, tmps[])

    x27 = _helper(a[1] & x10, qr)
    x28 = _helper(x27 ^ x16, qr)
    x29 = _helper(a[2] ^ x9, qr)
    x30 = _helper(x29 ^ x18, qr)
    x31 = _helper(a[3] & x30, qr)
    x32 = _helper(x28 ^ x31, qr)
    x33 = _helper(x24 ^ x32, qr)
    x34 = _helper(a[1] & x33, qr)
    x35 = _helper(x23 ^ x34, qr)
    x36 = _helper(a[3] | x33, qr)
    x37 = _helper(x35 ^ x36, qr)
    x38 = _helper(a[5] & x37, qr)
    x39 = _helper(x32 ^ x38, output=outs[3])
    # *out3 ^= _helper(x39, tmps[])

    x40 = _helper(x25 ^ x37, qr)
    _ = _helper(x40 ^ x39, output=outs[2])
    # *out2 ^= _helper(x41, tmps[39])

    return qr


@build_gate("DES_S5", [], lambda: 10)
def s5() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = qr.new_wires(4, QBoolArray)
    # tmps = qr.new_wires(58, QBoolArray)
    # qr.set_ancillae(tmps)

    x0 = _helper(~a[5], qr)
    x1 = _helper(~a[2], qr)
    x2 = _helper(x0 | x1, qr)
    x3 = _helper(x2 ^ a[3], qr)
    x4 = _helper(a[0] & x2, qr)
    x5 = _helper(x3 ^ x4, qr)
    x6 = _helper(a[5] | a[3], qr)
    x7 = _helper(x6 ^ a[2], qr)
    x8 = _helper(a[2] | x6, qr)
    x9 = _helper(a[0] | x8, qr)
    x10 = _helper(x7 ^ x9, qr)
    x11 = _helper(a[4] & x10, qr)
    x12 = _helper(x5 ^ x11, qr)
    x13 = _helper(~x3, qr)
    x14 = _helper(x13 & a[5], qr)
    x15 = _helper(a[0] | x14, qr)
    x16 = _helper(x7 ^ x15, qr)
    x17 = _helper(a[4] | x16, qr)
    x18 = _helper(x9 ^ x17, qr)
    x19 = _helper(a[1] | x18, qr)
    _ = _helper(x12 ^ x19, output=outs[2])
    # *out2 ^= _helper(x20, tmps[])

    x21 = _helper(x1 | x14, qr)
    x22 = _helper(x21 ^ a[5], qr)
    x23 = _helper(a[3] ^ x21, qr)
    x24 = _helper(a[0] & x23, qr)
    x25 = _helper(x22 ^ x24, qr)
    x26 = _helper(a[0] ^ x10, qr)
    x27 = _helper(x26 & x21, qr)
    x28 = _helper(a[4] | x27, qr)
    x29 = _helper(x25 ^ x28, qr)
    x30 = _helper(a[3] | x26, qr)
    x31 = _helper(~x30, qr)
    x32 = _helper(a[1] | x31, qr)
    x33 = _helper(x29 ^ x32, output=outs[1])
    # *out1 ^= _helper(x33, tmps[])

    x34 = _helper(x1 ^ x14, qr)
    x35 = _helper(a[0] & x34, qr)
    x36 = _helper(x13 ^ x35, qr)
    x37 = _helper(x4 ^ x6, qr)
    x38 = _helper(x37 & x33, qr)
    x39 = _helper(a[4] | x38, qr)
    x40 = _helper(x36 ^ x39, qr)
    x41 = _helper(x1 ^ x4, qr)
    x42 = _helper(x41 & x15, qr)
    x43 = _helper(x3 & x26, qr)
    x44 = _helper(a[4] & x43, qr)
    x45 = _helper(x42 ^ x44, qr)
    x46 = _helper(a[1] | x45, qr)
    x47 = _helper(x40 ^ x46, output=outs[0])
    # *out0 ^= _helper(x47, tmps[])

    x48 = _helper(x23 & x47, qr)
    x49 = _helper(x48 ^ x4, qr)
    x50 = _helper(x10 ^ x29, qr)
    x51 = _helper(x50 | x49, qr)
    x52 = _helper(a[4] & x51, qr)
    x53 = _helper(x49 ^ x52, qr)
    x54 = _helper(x13 ^ x18, qr)
    x55 = _helper(x54 ^ x33, qr)
    x56 = _helper(x3 ^ x15, qr)
    x57 = _helper(x56 & x29, qr)
    x58 = _helper(a[4] & x57, qr)
    x59 = _helper(x55 ^ x58, qr)
    x60 = _helper(a[1] | x59, qr)
    _ = _helper(x53 ^ x60, output=outs[3])
    # *out3 ^= _helper(x61, qr)

    return qr


@build_gate("DES_S6", [], lambda: 10)
def s6() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = qr.new_wires(4, QBoolArray)

    x0 = _helper(~a[1], qr)
    x1 = _helper(~a[4], qr)
    x2 = _helper(a[1] ^ a[5], qr)
    x3 = _helper(x2 ^ x1, qr)
    x4 = _helper(x3 ^ a[0], qr)
    x5 = _helper(a[4] & a[5], qr)
    x6 = _helper(x5 | x0, qr)
    x7 = _helper(a[4] & x4, qr)
    x8 = _helper(a[0] & x7, qr)
    x9 = _helper(x6 ^ x8, qr)
    x10 = _helper(a[3] & x9, qr)
    x11 = _helper(x4 ^ x10, qr)
    x12 = _helper(a[5] ^ x9, qr)
    x13 = _helper(x12 & a[0], qr)
    x14 = _helper(a[1] & a[5], qr)
    x15 = _helper(x14 ^ a[4], qr)
    x16 = _helper(a[0] & x15, qr)
    x17 = _helper(x1 ^ x16, qr)
    x18 = _helper(a[3] | x17, qr)
    x19 = _helper(x13 ^ x18, qr)
    x20 = _helper(a[2] & x19, qr)
    _ = _helper(x11 ^ x20, output=outs[1])
    # *out1 ^= _helper(x21, output = out[1])

    x22 = _helper(a[5] ^ x17, qr)
    x23 = _helper(a[0] & x22, qr)
    x24 = _helper(a[4] ^ x23, qr)
    x25 = _helper(a[1] ^ x16, qr)
    x26 = _helper(x25 | x5, qr)
    x27 = _helper(a[3] & x26, qr)
    x28 = _helper(x24 ^ x27, qr)
    x29 = _helper(~x25, qr)
    x30 = _helper(a[5] | x28, qr)
    x31 = _helper(~x30, qr)
    x32 = _helper(a[3] & x31, qr)
    x33 = _helper(x29 ^ x32, qr)
    x34 = _helper(a[2] & x33, qr)
    _ = _helper(x28 ^ x34, output=outs[3])
    # *out3 ^= _helper(x35, qr)

    x36 = _helper(x5 ^ x33, qr)
    x37 = _helper(a[4] & x22, qr)
    x38 = _helper(x37 ^ x4, qr)
    x39 = _helper(a[3] | x38, qr)
    x40 = _helper(x36 ^ x39, qr)
    x41 = _helper(x15 | x23, qr)
    x42 = _helper(x41 ^ x0, qr)
    x43 = _helper(x14 ^ x23, qr)
    x44 = _helper(x43 ^ x30, qr)
    x45 = _helper(a[3] | x44, qr)
    x46 = _helper(x42 ^ x45, qr)
    x47 = _helper(a[2] | x46, qr)
    _ = _helper(x40 ^ x47, output=outs[0])
    # *out0 ^= _helper(x48, qr)

    x49 = _helper(x4 | x37, qr)
    x50 = _helper(x49 ^ x5, qr)
    x51 = _helper(x7 & x30, qr)
    x52 = _helper(a[3] | x51, qr)
    x53 = _helper(x50 ^ x52, qr)
    x54 = _helper(x29 & x42, qr)
    x55 = _helper(a[2] | x54, qr)
    _ = _helper(x53 ^ x55, output=outs[2])
    # *out2 ^= _helper(x56, qr)

    return qr


@build_gate("DES_S7", [], lambda: 10)
def s7() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = qr.new_wires(4, QBoolArray)

    x0 = _helper(~a[1], qr)
    x1 = _helper(~a[4], qr)
    x2 = _helper(a[1] & a[3], qr)
    x3 = _helper(x2 ^ a[4], qr)
    x4 = _helper(x3 ^ a[2], qr)
    x5 = _helper(a[3] & x3, qr)
    x6 = _helper(x5 ^ a[1], qr)
    x7 = _helper(a[2] & x6, qr)
    x8 = _helper(a[0] ^ x7, qr)
    x9 = _helper(a[5] | x8, qr)
    x10 = _helper(x4 ^ x9, qr)
    x11 = _helper(a[3] & x1, qr)
    x12 = _helper(x11 | a[1], qr)
    x13 = _helper(a[1] | x1, qr)
    x14 = _helper(a[2] & x13, qr)
    x15 = _helper(x12 ^ x14, qr)
    x16 = _helper(x5 ^ x10, qr)
    x17 = _helper(a[5] | x16, qr)
    x18 = _helper(x15 ^ x17, qr)
    x19 = _helper(a[0] & x18, qr)
    x20 = _helper(x10 ^ x19, output=outs[0])
    # *out0 ^= _helper(x20, qr)

    x21 = _helper(a[1] | x20, qr)
    x22 = _helper(x21 ^ x5, qr)
    x23 = _helper(x22 ^ x14, qr)
    x24 = _helper(x4 ^ x5, qr)
    x25 = _helper(x24 | x11, qr)
    x26 = _helper(a[5] | x25, qr)
    x27 = _helper(x23 ^ x26, qr)
    x28 = _helper(x0 & x18, qr)
    x29 = _helper(x22 & x25, qr)
    x30 = _helper(a[5] & x29, qr)
    x31 = _helper(x28 ^ x30, qr)
    x32 = _helper(a[0] | x31, qr)
    _ = _helper(x27 ^ x32, output=outs[3])
    # *out3 ^= _helper(x33, qr)

    x34 = _helper(a[3] & x15, qr)
    x35 = _helper(x34 | x0, qr)
    x36 = _helper(a[5] & x35, qr)
    x37 = _helper(x10 ^ x36, qr)
    x38 = _helper(a[3] & x12, qr)
    x39 = _helper(a[2] | x6, qr)
    x40 = _helper(x38 ^ x39, qr)
    x41 = _helper(x0 | x23, qr)
    x42 = _helper(a[5] | x41, qr)
    x43 = _helper(x40 ^ x42, qr)
    x44 = _helper(a[0] | x43, qr)
    x45 = _helper(x37 ^ x44, output=outs[1])
    # *out1 ^= _helper(x45, qr)

    x46 = _helper(x7 ^ x43, qr)
    x47 = _helper(x5 ^ x14, qr)
    x48 = _helper(a[5] | x47, qr)
    x49 = _helper(x46 ^ x48, qr)
    x50 = _helper(x18 ^ x43, qr)
    x51 = _helper(a[3] ^ x24, qr)
    x52 = _helper(x51 & x45, qr)
    x53 = _helper(a[5] & x52, qr)
    x54 = _helper(x50 ^ x53, qr)
    x55 = _helper(a[0] | x54, qr)
    _ = _helper(x49 ^ x55, output=outs[2])
    # *out2 ^= _helper(x56, qr)

    return qr


@build_gate("DES_S8", [], lambda: 10)
def s8() -> QRoutine:
    qr = QRoutine()
    a = qr.new_wires(6, QBoolArray)
    outs = qr.new_wires(4, QBoolArray)

    x0 = _helper(~a[0], qr)
    x1 = _helper(~a[3], qr)
    x2 = _helper(a[2] ^ x0, qr)
    x3 = _helper(a[2] | x0, qr)
    x4 = _helper(x3 ^ x1, qr)
    x5 = _helper(a[4] | x4, qr)
    x6 = _helper(x2 ^ x5, qr)
    x7 = _helper(x0 | x4, qr)
    x8 = _helper(x1 ^ x7, qr)
    x9 = _helper(a[4] & x8, qr)
    x10 = _helper(x7 ^ x9, qr)
    x11 = _helper(a[1] & x10, qr)
    x12 = _helper(x6 ^ x11, qr)
    x13 = _helper(x5 ^ x8, qr)
    x14 = _helper(x2 & x8, qr)
    x15 = _helper(a[4] & x7, qr)
    x16 = _helper(x14 ^ x15, qr)
    x17 = _helper(a[1] | x16, qr)
    x18 = _helper(x13 ^ x17, qr)
    x19 = _helper(a[5] | x18, qr)
    _ = _helper(x12 ^ x19, output=outs[0])
    # *out0 ^= _helper(x20, qr)

    x21 = _helper(a[4] | x2, qr)
    x22 = _helper(x21 & x1, qr)
    x23 = _helper(~a[2], qr)
    x24 = _helper(x23 & x7, qr)
    x25 = _helper(a[4] & x3, qr)
    x26 = _helper(x24 ^ x25, qr)
    x27 = _helper(a[1] | x26, qr)
    x28 = _helper(x22 ^ x27, qr)
    x29 = _helper(a[5] & x28, qr)
    _ = _helper(x12 ^ x29, output=outs[3])
    # *out3 ^= _helper(x30, qr)

    x31 = _helper(x4 ^ x5, qr)
    x32 = _helper(x31 ^ x21, qr)
    x33 = _helper(a[3] | x12, qr)
    x34 = _helper(a[1] & x33, qr)
    x35 = _helper(x32 ^ x34, qr)
    x36 = _helper(a[0] & x32, qr)
    x37 = _helper(x36 ^ x7, qr)
    x38 = _helper(a[0] ^ x22, qr)
    x39 = _helper(x38 & x6, qr)
    x40 = _helper(a[1] & x39, qr)
    x41 = _helper(x37 ^ x40, qr)
    x42 = _helper(a[5] | x41, qr)
    _ = _helper(x35 ^ x42, output=outs[2])
    # *out2 ^= _helper(x43, qr)

    x44 = _helper(a[0] ^ x9, qr)
    x45 = _helper(x44 ^ x21, qr)
    x46 = _helper(~x6, qr)
    x47 = _helper(x46 & x7, qr)
    x48 = _helper(a[1] | x47, qr)
    x49 = _helper(x45 ^ x48, qr)
    x50 = _helper(x18 ^ x28, qr)
    x51 = _helper(x50 | x37, qr)
    x52 = _helper(a[5] & x51, qr)
    _ = _helper(x49 ^ x52, output=outs[1])
    # *out1 ^= _helper(x53, qr)

    return qr


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
