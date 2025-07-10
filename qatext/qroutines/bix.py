from ctypes import ArgumentError
from math import ceil, log2
from typing import List

from qat.lang.AQASM.gates import CNOT, SWAP, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from qatext.qroutines import qregs_init
from qatext.qroutines.arith import adder
from qatext.qroutines.qubitshuffle import rotate


@build_gate("nXOR", [int], lambda n: 2 * n)
def nxor(n: int):
    qrout = QRoutine()
    qwc = qrout.new_wires(n)
    qwt = qrout.new_wires(n)

    for target, control in zip(qwc, qwt):
        qrout.apply(CNOT, target, control)

    return qrout


# @build_gate("BIX", [int, int], arity=lambda n1, n2: n1 + (n1 + 1) * ceil(log2(n2)))
@build_gate("BIX", [int, int, bool])
def bix_fixed_weight_v1(n: int, weight: int, idx_start_at_one: bool):
    """Given a bitstring of length `n`, having exactly `weight` qubits set
    to 1, store into `weight` registers the indexes of the 1's of the
    bitstring, and `n - weight` registers the weight of the 0's of the
    bitstring.

    It should be applied to the following registers:
    - qreg of length `n`, containing `weight` 1's
    - `weight` qregs, each of size `log2(n)`
    - `n - weight` qregs, each of size `log2(n)`
    - `idx_start_at_one` if True, start indexing the array results from 1, else from 0

    It uses an additional ancilla register, reset to all zeros after
    - one qreg of size `log2(n)`
    If `weight` is equal to 1 or n-1, it uses an additional support array

    Internally, it invokes left rotate circuit and addition circuits; last one
    is abstract and must be specialized.

    """

    if weight < 1 or weight >= n:
        raise ArgumentError("Weight should be >=1 and < n, given %s" % weight)
    qrout = QRoutine()
    if idx_start_at_one:
        l2n = int(ceil(log2(n + 1)))
    else:
        l2n = int(ceil(log2(n)))

    qrout.arity = n * l2n + n

    wreg = qrout.new_wires(n)
    oregs = []
    zregs = []
    for i in range(weight):
        oregs.append(qrout.new_wires(l2n))
    for i in range(n - weight):
        zregs.append(qrout.new_wires(l2n))
    if weight == 1 or weight == n - 1:
        oregs.append(qrout.new_wires(l2n))
        zregs.append(qrout.new_wires(l2n))
        qrout.set_ancillae(oregs[-1])
        qrout.set_ancillae(zregs[-1])
    # the register that will hold the constants +1 and -n
    const = qrout.new_wires(l2n)
    qrout.set_ancillae(const)

    #
    qset1 = qregs_init.initialize_qureg_given_int(1, l2n, little_endian=False)
    qadd = adder(l2n, l2n, False, False)
    qleftrotones = rotate.reg_reversal(len(oregs), l2n, 1)
    qleftrotzeros = rotate.reg_reversal(len(zregs), l2n, 1)
    final_clean = n if idx_start_at_one else n - 1
    qsetfinal = qregs_init.initialize_qureg_given_int(final_clean,
                                                      l2n,
                                                      little_endian=False)

    qrout.apply(qset1, const)
    for i in range(n):
        if i != 0 or (i == 0 and idx_start_at_one):
            qrout.apply(qadd, const, oregs[0])
            qrout.apply(qadd, const, zregs[0])

        # if wreg[i] is 1, we left rotate the ones
        qrout.apply(qleftrotones.ctrl(1), wreg[i], *oregs)
        # ... and add to the ones register
        qrout.apply(qadd.ctrl(1), wreg[i], oregs[-1], oregs[0])

        # ...otw, we left rotate the zeros
        qrout.apply(X, wreg[i])
        qrout.apply(qleftrotzeros.ctrl(1), wreg[i], *zregs)
        qrout.apply(qadd.ctrl(1), wreg[i], zregs[-1], zregs[0])
        qrout.apply(X, wreg[i])

    # reset const register to 0
    qrout.apply(qset1.dag(), const)

    # set it to value n
    qrout.apply(qsetfinal, const)
    for qreg in (oregs[0], zregs[0]):
        # The topmost register, qreg, should be decreased by the constant value
        # n, stored in the the register const. However, when we use the
        # sub(qreg, const) circuit, the result is stored in const.
        #
        # Additionally, note that val(qreg) = n + delta, delta >= 0; i.e., the
        # topmost register is always greater than n.
        #
        # So first we swap the two qregs; now val(qreg) = n; val(const) = n + delta
        for qb1, qb2 in zip(qreg, const):
            qrout.apply(SWAP, qb1, qb2)
        # then we negate const; val(const) = complement(n+delta)
        for qb in const:
            qrout.apply(X, qb)
        # then, we add to it the constant register and complement again, obtaining
        # val(const) = delta
        qrout.apply(qadd, qreg, const)
        for qb in const:
            qrout.apply(X, qb)
        # then, we switch again: val(qreg) = delta; val(const) = n
        for qb1, qb2 in zip(qreg, const):
            qrout.apply(SWAP, qb1, qb2)
    # reset const register to 0
    qrout.apply(qsetfinal.dag(), const)

    if weight == 1 or weight == n - 1:
        # there is an extra register
        qrout.apply(qleftrotzeros, *zregs)
        qrout.apply(qleftrotones, *oregs)

    return qrout


@build_gate(
    "BIX", [int, int, bool], lambda n, _, x: n + n * (n.bit_length() if x else
                                                      (n - 1).bit_length()))
def bix_fixed_weight_v2(n: int, weight: int, idx_start_at_one: bool):
    """Given a bitstring of length `n`, having exactly `weight` qubits set
    to 1, store into `weight` registers the indexes of the 1's of the
    bitstring, and `n - weight` registers the weight of the 0's of the
    bitstring.

    It should be applied to the following registers:
    - qreg of length `n`, containing `weight` 1's
    - `weight` qregs, each of size `log2(n)`
    - `n - weight` qregs, each of size `log2(n)`
    - `idx_start_at_one` if True, start indexing the array results from 1, else from 0

    It uses an additional ancilla register, reset to all zeros after
    - one qreg of size `log2(n)`
    If `weight` is equal to 1 or n-1, it uses an additional support array

    Internally, it invokes left rotate circuit and addition circuits; last one
    is abstract and must be specialized.

    """

    if weight < 1 or weight >= n:
        raise ArgumentError("Weight should be >=1 and < n, given {}" % weight)
    qrout = QRoutine()
    if idx_start_at_one:
        l2n = int(ceil(log2(n + 1)))
    else:
        l2n = int(ceil(log2(n)))

    wreg = qrout.new_wires(n)
    oregs = []
    zregs = []
    for i in range(weight):
        oregs.append(qrout.new_wires(l2n))
    for i in range(n - weight):
        zregs.append(qrout.new_wires(l2n))

    ancillae1 = qrout.new_wires(l2n)
    qrout.set_ancillae(ancillae1)
    oregs.append(ancillae1)
    ancillae2 = qrout.new_wires(l2n)
    qrout.set_ancillae(ancillae2)
    zregs.append(ancillae2)
    # if weight == 1 or weight == n - 1:
    #     oregs.append(qrout.new_wires(l2n))
    #     zregs.append(qrout.new_wires(l2n))
    #     qrout.set_ancillae(oregs[-1])
    #     qrout.set_ancillae(zregs[-1])
    # the register that will hold the constants +1 and -n
    const = qrout.new_wires(l2n)
    qrout.set_ancillae(const)

    #
    qset1 = qregs_init.initialize_qureg_given_int(1, l2n, little_endian=False)
    qadd = adder(l2n, l2n, False, False)
    qxor = nxor(l2n)
    qleftrotones = rotate.reg_reversal(len(oregs), l2n, 1)
    qleftrotzeros = rotate.reg_reversal(len(zregs), l2n, 1)
    final_clean = n if idx_start_at_one else n - 1
    qsetfinal = qregs_init.initialize_qureg_given_int(final_clean,
                                                      l2n,
                                                      little_endian=False)

    qrout.apply(qset1, const)
    for i in range(n):
        if i != 0 or (i == 0 and idx_start_at_one):
            qrout.apply(qadd, const, oregs[0])
            qrout.apply(qadd, const, zregs[0])

        # if wreg[i] is 1, we left rotate the ones
        qrout.apply(qleftrotones.ctrl(1), wreg[i], *oregs)
        # ... and add to the ones register
        qrout.apply(qxor.ctrl(1), wreg[i], oregs[-1], oregs[0])

        # ...otw, we left rotate the zeros
        qrout.apply(X, wreg[i])
        qrout.apply(qleftrotzeros.ctrl(1), wreg[i], *zregs)
        qrout.apply(qxor.ctrl(1), wreg[i], zregs[-1], zregs[0])
        qrout.apply(X, wreg[i])

    # reset const register to 0
    qrout.apply(qset1.dag(), const)

    # set it to value n
    qrout.apply(qsetfinal, const)
    for qreg in (oregs[0], zregs[0]):
        # The topmost register, qreg, should be decreased by the constant value
        # n, stored in the the register const. However, when we use the
        # sub(qreg, const) circuit, the result is stored in const.
        #
        # Additionally, note that val(qreg) = n + delta, delta >= 0; i.e., the
        # topmost register is always greater than n.
        #
        # So first we swap the two qregs; now val(qreg) = n; val(const) = n + delta
        for qb1, qb2 in zip(qreg, const):
            qrout.apply(SWAP, qb1, qb2)
        # then we negate const; val(const) = complement(n+delta)
        for qb in const:
            qrout.apply(X, qb)
        # then, we add to it the constant register and complement again, obtaining
        # val(const) = delta
        qrout.apply(qadd, qreg, const)
        for qb in const:
            qrout.apply(X, qb)
        # then, we switch again: val(qreg) = delta; val(const) = n
        for qb1, qb2 in zip(qreg, const):
            qrout.apply(SWAP, qb1, qb2)
    # reset const register to 0
    qrout.apply(qsetfinal.dag(), const)

    # if weight == 1 or weight == n-1:
    # there is an extra register
    qrout.apply(qleftrotzeros, *zregs)
    qrout.apply(qleftrotones, *oregs)

    return qrout

@build_gate(
    "BIX", [int, int, int, List], lambda n, m, w, x: n + n * m)
def bix_fixed_weight_v3(n: int, m: int, weight: int, elems: List):
    """Given a bitstring of length `n`, having exactly `weight` qubits set to
    1, store into `weight` registers the values `elems[i]` if `dicke[i] == 1`,
    and `n - weight` registers the values `elems[i]` if `dicke[i] == 0`.

    It should be applied to the following registers:
    - qreg_dicke: the register containing the dicke state

    It uses an additional ancilla register, reset to all zeros after
    - one qreg of size `log2(n)`
    If `weight` is equal to 1 or n-1, it uses an additional support array

    Internally, it invokes left rotate circuit and addition circuits; last one
    is abstract and must be specialized.

    """

    if weight < 1 or weight >= n:
        raise ArgumentError("Weight should be >=1 and < n, given {}" % weight)
    elems_diffs = [elems[0]] + [j - i for i, j in zip(elems, elems[1:])]
    # print(f"elems {elems}")
    # print(f"elems_diffs {elems_diffs}")
    # print(f"m {m}")

    qrout = QRoutine()
    wreg = qrout.new_wires(n)
    oregs = []
    zregs = []
    for i in range(weight):
        oregs.append(qrout.new_wires(m))
    for i in range(n - weight):
        zregs.append(qrout.new_wires(m))
    ancillae1 = qrout.new_wires(m)
    qrout.set_ancillae(ancillae1)
    oregs.append(ancillae1)
    ancillae2 = qrout.new_wires(m)
    qrout.set_ancillae(ancillae2)
    zregs.append(ancillae2)
    # the register that will hold the constants +1 and -n
    # in theory can be smaller than this
    const = qrout.new_wires(m)
    qrout.set_ancillae(const)

    #
    qadd = adder(m, m, False, False)
    qxor = nxor(m)
    qleftrotones = rotate.reg_reversal(len(oregs), m, 1)
    qleftrotzeros = rotate.reg_reversal(len(zregs), m, 1)

    # _otmp = [0] * (weight+1)
    # _ztmp = [0] * (n-weight+1)

    for i in range(n):
        qset1 = qregs_init.initialize_qureg_given_int(elems_diffs[i], m, little_endian=False)
        qrout.apply(qset1, const)
        # print(f"set const to {elems_diffs[i]}")
        if elems_diffs[i] != 0:
            # print("oregs[0] += const")
            # _otmp[0] += elems_diffs[i]
            # print(f"oregs[0] = {_otmp[0]}")
            # print("zregs[0] += const")
            # _ztmp[0] += elems_diffs[i]
            # print(f"zregs[0] = {_ztmp[0]}")
            qrout.apply(qadd, const, oregs[0])
            qrout.apply(qadd, const, zregs[0])

        # if wreg[i] is 1, we left rotate the ones
        qrout.apply(qleftrotones.ctrl(1), wreg[i], *oregs)
        # ... and copy to the first register 
        qrout.apply(qxor.ctrl(1), wreg[i], oregs[-1], oregs[0])

        # ...otw, we left rotate the zeros
        qrout.apply(X, wreg[i])
        qrout.apply(qleftrotzeros.ctrl(1), wreg[i], *zregs)
        qrout.apply(qxor.ctrl(1), wreg[i], zregs[-1], zregs[0])
        qrout.apply(X, wreg[i])
        # reset const register to 0
        qrout.apply(qset1.dag(), const)

    # final_clean = n if idx_start_at_one else n - 1
    final_clean = elems[-1]
    # set it to value n
    qsetfinal = qregs_init.initialize_qureg_given_int(final_clean,
                                                      m,
                                                      little_endian=False)
    qrout.apply(qsetfinal, const)
    for qreg in (oregs[0], zregs[0]):
        # The topmost register, qreg, should be decreased by the constant value
        # n, stored in the the register const. However, when we use the
        # sub(qreg, const) circuit, the result is stored in const.
        #
        # Additionally, note that val(qreg) = n + delta, delta >= 0; i.e., the
        # topmost register is always greater than n.
        #
        # So first we swap the two qregs; now val(qreg) = n; val(const) = n + delta
        for qb1, qb2 in zip(qreg, const):
            qrout.apply(SWAP, qb1, qb2)
        # then we negate const; val(const) = complement(n+delta)
        for qb in const:
            qrout.apply(X, qb)
        # then, we add to it the constant register and complement again, obtaining
        # val(const) = delta
        qrout.apply(qadd, qreg, const)
        for qb in const:
            qrout.apply(X, qb)
        # then, we switch again: val(qreg) = delta; val(const) = n
        for qb1, qb2 in zip(qreg, const):
            qrout.apply(SWAP, qb1, qb2)
    # reset const register to 0
    qrout.apply(qsetfinal.dag(), const)

    # if weight == 1 or weight == n-1:
    # there is an extra register
    qrout.apply(qleftrotzeros, *zregs)
    qrout.apply(qleftrotones, *oregs)

    return qrout
