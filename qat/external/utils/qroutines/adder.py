# -*- coding: utf-8 -*-
"""
Ripple adder example based on Cuccaro et al., quant-ph/0410184.
"""

import itertools
import logging

from qat.lang.AQASM import CCNOT, CNOT, QRoutine, X
from qat.lang.AQASM.misc import build_gate

# from .fake import fake

LOGGER = logging.getLogger(__name__)


def _common_init(a_l, b_l, overflow_qbit, little_endian):
    bits = min(a_l, b_l)
    # b_l contains the result
    b_is_bigger = b_l > bits

    qfun = QRoutine()
    a = qfun.new_wires(a_l)
    b = qfun.new_wires(b_l)
    if not little_endian:
        a.reverse()
        b.reverse()
    # Just for graphical purposes
    # for i, aq in enumerate(a):
    #     qfun.apply(fake(f"a{i}"), aq)
    # for i, bq in enumerate(b):
    #     qfun.apply(fake(f"b{i}"), bq)
    LOGGER.debug("a %s", a)
    LOGGER.debug("b %s", b)
    if b_l > 1:
        cin = qfun.new_wires(1)
        qfun.set_ancillae(cin)
        # qfun.apply(fake("cin"), cin[0])
        LOGGER.debug("cin %s", cin)
    else:
        cin = None

    if overflow_qbit:
        cout = qfun.new_wires(1)
        # qfun.apply(fake("cout"), cout[0])
        LOGGER.debug("cout %s", cout)
    else:
        cout = None

    return qfun, a, b, cin, cout, bits, b_is_bigger


def _common(qfun, a, b, cin, cout, b_is_bigger, bits, overflow_qbit,
            little_endian):
    a_l = len(a)
    b_l = len(b)
    if b_l == 1:
        qfun.apply(CNOT, a[0], b[0])
        if overflow_qbit:
            qfun.apply(X, b[0])
            qfun.apply(CCNOT, a[0], b[0], cout[0])
            qfun.apply(X, b[0])
            if a_l > bits:
                qfun.apply(CNOT, a[1], cout[0])
        return None, None, None

    sub = 0 if (overflow_qbit or b_l > a_l) else 1
    LOGGER.debug(f"sub is {sub}")
    end = bits - 1
    ends = end - sub
    mrange = range(0, ends)
    LOGGER.debug("mrange %s", mrange)
    return mrange, end, ends


def _maj_chain(qfun, a, b, cin, mrange):
    LOGGER.debug("MAJ %d, %d, %d", cin[0], b[0], a[0])
    qfun.apply(_majority(f"cin, b{0}, a{0}"), cin[0], b[0], a[0])
    for j in mrange:
        LOGGER.debug("j is %d", j)
        LOGGER.debug("MAJ %d, %d, %d", a[j], b[j + 1], a[j + 1])
        qfun.apply(_majority(f"a{j}, b{j+1}, a{j+1}"), a[j], b[j + 1],
                   a[j + 1])


def _maj_chain_dag(qfun, a, b, cin, mrange):
    for j in reversed(mrange):
        LOGGER.debug("j is %d", j)
        LOGGER.debug("MAJD %d, %d, %d", a[j], b[j + 1], a[j + 1])
        qfun.apply(
            _majority(f"a{j}, b{j+1}, a{j+1}").dag(), a[j], b[j + 1], a[j + 1])
    LOGGER.debug("MAJD %d, %d, %d", cin[0], b[0], a[0])
    qfun.apply(_majority(f"cin, b{0}, a{0}").dag(), cin[0], b[0], a[0])


def _middle_logic(qfun, a, b, cin, cout, end, ends, little_endian,
                  overflow_qbit, b_is_bigger):
    a_l = len(a)
    b_l = len(b)
    # MIDDLE LOGIC ###
    if not b_is_bigger:
        outbit = cout[0] if overflow_qbit else b[end]
        LOGGER.debug("b is not bigger")
        LOGGER.debug("CNOT %d, %d", a[end], outbit)

        qfun.apply(CNOT, a[ends], outbit)
        if not overflow_qbit and a_l == b_l:
            # Simple modulo 2^b_l operation, as in Cuccaro's paper
            LOGGER.debug("CNOT %d, %d", a[ends], outbit)
            qfun.apply(CNOT, a[end], outbit)
        elif a_l > b_l:
            LOGGER.debug("CNOT %d, %d", a[ends + 1], outbit)
            qfun.apply(CNOT, a[ends + 1], outbit)
    else:
        # b_l > bits -> b extends past end
        # Additional logic to take care of different size regs, not
        # present in Cuccaro
        outbit = cout[0] if overflow_qbit else b[-1]
        LOGGER.debug("b is bigger")
        nslice = b[end + 2:b_l:1]
        LOGGER.debug("nslice %s", nslice)
        chain = itertools.chain(nslice, cout) if overflow_qbit else nslice
        LOGGER.debug("CNOT %d, %d", a[end], b[end + 1])
        qfun.apply(CNOT, a[ends], b[end + 1])
        prv_tgt_1 = a[ends]
        prv_tgt = b[end + 1]
        for cur_tgt in chain:
            LOGGER.debug("X %s", prv_tgt)
            qfun.apply(X, prv_tgt)
            LOGGER.debug("CCNOT %s %s %s", prv_tgt_1, prv_tgt, cur_tgt)
            qfun.apply(CCNOT, prv_tgt_1, prv_tgt, cur_tgt)
            LOGGER.debug("X %s", prv_tgt)
            qfun.apply(X, prv_tgt)
            prv_tgt = cur_tgt


def _unmaj_chain(qfun, a, b, cin, mrange):
    # UNM CHAIN ###
    for j in reversed(mrange):
        LOGGER.debug("j is %d", j)
        LOGGER.debug("UNM %d, %d, %d", a[j], b[j + 1], a[j + 1])
        qfun.apply(_unmajority(f"a{j}, b{j+1}, a{j+1}"), a[j], b[j + 1],
                   a[j + 1])
    LOGGER.debug("UNM %d, %d, %d", cin[0], b[0], a[0])
    qfun.apply(_unmajority(f"cin, b{0}, a{0}"), cin[0], b[0], a[0])


@build_gate("MCOMP", [int, int, bool])
def comparator(a_l: int, b_l: int, little_endian=True):
    overflow_qbit = True
    qfun, a, b, cin, cout, bits, b_is_bigger = _common_init(
        a_l, b_l, overflow_qbit, little_endian)
    for qb in a:
        qfun.apply(X, qb)

    mrange, end, ends = _common(qfun, a, b, cin, cout, b_is_bigger, bits,
                                overflow_qbit, little_endian)
    if mrange is not None:
        _maj_chain(qfun, a, b, cin, mrange)
        _middle_logic(qfun, a, b, cin, cout, end, ends, little_endian,
                      overflow_qbit, b_is_bigger)
        _maj_chain_dag(qfun, a, b, cin, mrange)

    for qb in a:
        qfun.apply(X, qb)

    return qfun


@build_gate("MSUB", [int, int, bool, bool])
def subtractor(a_l: int, b_l: int, overflow_qbit=False, little_endian=True):
    qfun, a, b, cin, cout, bits, b_is_bigger = _common_init(
        a_l, b_l, overflow_qbit, little_endian)
    for qb in a:
        qfun.apply(X, qb)

    mrange, end, ends = _common(qfun, a, b, cin, cout, b_is_bigger, bits,
                                overflow_qbit, little_endian)
    if mrange is not None:
        _maj_chain(qfun, a, b, cin, mrange)
        _middle_logic(qfun, a, b, cin, cout, end, ends, little_endian,
                      overflow_qbit, b_is_bigger)
        _unmaj_chain(qfun, a, b, cin, mrange)
    # out = (b, cout) if cout is not None else (b, )
    # for qb in itertools.chain(a, *out):
    for qb in itertools.chain(a, b):
        qfun.apply(X, qb)

    return qfun


@build_gate("MADD", [int, int, bool, bool])
def adder(a_l: int, b_l: int, overflow_qbit=False, little_endian=True):
    qfun, a, b, cin, cout, bits, b_is_bigger = _common_init(
        a_l, b_l, overflow_qbit, little_endian)
    mrange, end, ends = _common(qfun, a, b, cin, cout, b_is_bigger, bits,
                                overflow_qbit, little_endian)
    if mrange is None:
        return qfun
    _maj_chain(qfun, a, b, cin, mrange)
    _middle_logic(qfun, a, b, cin, cout, end, ends, little_endian,
                  overflow_qbit, b_is_bigger)
    _unmaj_chain(qfun, a, b, cin, mrange)

    return qfun


@build_gate("MAJ", [str])
def _majority(name):
    """Majority gate."""
    qfun = QRoutine()
    c = qfun.new_wires(1)[0]
    b = qfun.new_wires(1)[0]
    a = qfun.new_wires(1)[0]
    qfun.apply(CNOT, a, b)
    qfun.apply(CNOT, a, c)
    qfun.apply(CCNOT, c, b, a)
    return qfun


@build_gate("UMA", [str])
def _unmajority(name):
    """Unmajority gate."""
    qfun = QRoutine()
    c = qfun.new_wires(1)[0]
    b = qfun.new_wires(1)[0]
    a = qfun.new_wires(1)[0]
    qfun.apply(CCNOT, c, b, a)
    qfun.apply(CNOT, a, c)
    qfun.apply(CNOT, c, b)
    return qfun
