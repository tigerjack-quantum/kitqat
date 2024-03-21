"""Set of algebraic routines."""
from qat.lang.AQASM.gates import CCNOT, CNOT, X
from qat.lang.AQASM.routines import QRoutine


def gcd_inv(n: str):
    """
    :param n: a bitstring of length k+1 containing the modulus of the field GF(2^k)/n(x)
    :
    """
    qrout = QRoutine()
