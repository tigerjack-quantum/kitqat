"""Implementations were taken from.

[1]
[2] Lecture notes not_04 from Crypto course
[3]
"""
from collections import deque

from qatext.qroutines.arith import cuccaro_arith as cuccadd
from qat.lang.AQASM.classarith import add_const, add_mod, add_const_mod
from qat.lang.AQASM.gates import CNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine

@build_gate("M_ADD", [int], arity=lambda x: x * 2 + 2)
def madd(nbits: int) -> QRoutine:
    """It perfoms |a>|b>|0>|g> -> |a>|(a+b) mod(n)>|0>|g> in Montgomery domain.
    Sizes | bits>| bits>|1>|1>.

    :param nbitstr: is the bitstring (in LITTLE ENDIAN format, i.e. element at index 0 is the LSB)
    of length d.

    The multiplication is therefore between two qreg of length d, mod
    int(nbitstr).

    Alg. 6.2 of [2] w/out the useless extension on A_d and without the final check on x >= n
    """

    qadd = cuccadd.adder.circuit_generator(
        nbits, nbits, overflow_qbit=True, little_endian=True
    )
