from ctypes import ArgumentError
from qat.external.qroutines.arith import adder
from qat.external.qroutines.qubitshuffle import rotate
from qat.lang.AQASM.gates import X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from qat.external.qroutines import qregs_init
from math import log2, ceil


# @build_gate("BIX", [int, int], arity=lambda n1, n2: n1 + (n1 + 1) * ceil(log2(n2)))
@build_gate("BIX", [int, int])
def bix_fixed_weight(n: int, weight: int):
    """Given a bitstring of length `n`, having exactly `weight` qubits set
    to 1, store into `weight` registers the indexes of the 1's of the
    bitstring, and `n - weight` registers the weight of the 0's of the
    bitstring.

    It should be applied to the following registers:
    - qreg of length `n`, containing `weight` 1's
    - `weight` qregs, each of size `log2(n)`
    - `n - weight` qregs, each of size `log2(n)`

    It uses an additional ancilla register, reset to all zeros after
    - one qreg of size `log2(n)`

    Internally, it invokes left rotate circuit and addition circuits; last one
    is abstract and must be specialized.

    """

    if weight < 1 or weight >= n:
        raise ArgumentError("Weight should be >=1 and < n, given {}" % weight)
    qrout = QRoutine()
    l2n = ceil(log2(n + 1))
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
    qrout.apply(qset1, const)
    qadd = adder(l2n, l2n, False, False)
    qleftrotones = rotate.reg_reversal(len(oregs), l2n, 1)
    qleftrotzeros = rotate.reg_reversal(len(zregs), l2n, 1)

    for i in range(n):
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
    qset1 = qregs_init.initialize_qureg_to_complement_of_int(
        n, l2n, little_endian=False
    )
    qrout.apply(qset1, const)
    qrout.apply(qadd, const, oregs[0])
    qrout.apply(qadd, const, zregs[0])

    if weight == 1 or weight == n-1:
        qrout.apply(qleftrotzeros, *zregs)
        qrout.apply(qleftrotones, *oregs)
    # reset const register to 0
    qrout.apply(qset1.dag(), const)

    return qrout
