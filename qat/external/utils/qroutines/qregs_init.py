import functools
import logging
from typing import TYPE_CHECKING, Sequence

from qat.lang.AQASM import QRoutine, X

from qat.external.utils.bits import conversion

if TYPE_CHECKING:
    from qat.lang.AQASM import QRegister

LOGGER = logging.getLogger(__name__)


# In big endian the MSB is on the left, while the LSB is on the right. So in
# big endian |100> would be equal to 4, while in little endian it will be equal
# to 1. Big endian is used by both ibm's qiskit and atos' qlm results. However,
# Atos qlm uses little endian for all other stuffs
def conditionally_initialize_qureg_given_bitarray(
    a_arr: Sequence[int],
    qreg: 'QRegister',
    qcontrols: 'QRegister',
    little_endian,
) -> QRoutine:
    qr = QRoutine()
    bits = qr.new_wires(len(a_arr))
    cbits = qr.new_wires(len(qcontrols)) if qcontrols is not None else None

    gate = X
    if qcontrols is not None:
        # for _ in range(len(qcontrols)):
        gate = gate.ctrl(len(cbits))
    part = functools.partial(qr.apply, gate)
    if qcontrols is not None:
        part = functools.partial(part, *cbits)
    mrange = zip(bits, reversed(a_arr)) if little_endian else zip(bits, a_arr)
    for qbit, aint in mrange:
        if aint == 1:
            part(qbit)
        elif aint != 0:
            raise ValueError(f"string {aint} contains non-binary value(s)")
    return qr


def conditionally_initialize_qureg_given_bitstring(a_str, qreg, qcontrols,
                                                   little_endian) -> QRoutine:
    a_list = [int(c) for c in a_str]
    # a_list = map(int, a_str)
    return conditionally_initialize_qureg_given_bitarray(
        a_list, qreg, qcontrols, little_endian)


def conditionally_initialize_qureg_to_complement_of_bitstring(
        a_str, qreg, qcontrols, qancilla, little_endian) -> QRoutine:
    a_n_str = conversion.get_negated_bistring(a_str)
    return conditionally_initialize_qureg_given_bitstring(
        a_n_str, qreg, qcontrols, little_endian)


def conditionally_initialize_qureg_to_complement_of_bitarray(
        a_str, qreg, qcontrols, qancilla, little_endian) -> QRoutine:
    a_n_str = conversion.get_negated_bitarray(a_str)
    return conditionally_initialize_qureg_given_bitarray(
        a_n_str, qreg, qcontrols, little_endian)


def initialize_qureg_given_bitarray(a_str, qreg, little_endian) -> QRoutine:
    """Given a binary string, initialize the qreg to the proper value
    corresponding to it. Basically, if a_str is 1011, the function negate bits
    0, 1 and 3 of the qreg. # 3->0; 2->1; 1->2; 0;3 Note that the qreg has the
    most significant bit in the rightmost part (little endian) of the qreg,
    i.e. the most significant bit is on qreg 0. In the circuit, it means that
    the most significant bits are the lower ones of the qreg

    :param a_str: the binary digits bit string
    :param qreg: the QuantumRegister on which the integer should be set
    :param circuit: the QuantumCircuit containing the q_reg

    :return False if no operation was performed, True if at least one operation
    was performed

    """
    return conditionally_initialize_qureg_given_bitarray(
        a_str, qreg, None, little_endian)


def initialize_qureg_given_bitstring(a_str, qreg, little_endian) -> QRoutine:
    """Given a binary string, initialize the qreg to the proper value
    corresponding to it. Basically, if a_str is 1011, the function negate bits
    0, 1 and 3 of the qreg. # 3->0; 2->1; 1->2; 0;3 Note that the qreg has the
    most significant bit in the rightmost part (little endian) of the qreg,
    i.e. the most significant bit is on qreg 0. In the circuit, it means that
    the most significant bits are the lower ones of the qreg

    :param a_str: the binary digits bit string
    :param qreg: the QuantumRegister on which the integer should be set
    :param circuit: the QuantumCircuit containing the q_reg

    :return False if no operation was performed, True if at least one operation
    was performed

    """
    return conditionally_initialize_qureg_given_bitstring(
        a_str, qreg, None, little_endian)


def initialize_qureg_given_int(a_int, qreg, little_endian):
    """Given a decimal integer, initialize the qreg to the proper value
    corresponding to it. Basically, if a_int is 11, i.e. 1011 in binary, the
    function negate bits 3, 2 and 0 of the qreg. Note that the qreg has the
    most significant bit in the leftmost part (big endian)

    :param a_int: the integer in decimal base
    :param qreg: the QuantumRegister on which the integer should be set
    :param circuit: the QuantumCircuit containing the q_reg

    """
    a_str = conversion.get_bitstring_from_int(a_int, len(qreg))
    return initialize_qureg_given_bitstring(a_str, qreg, little_endian)


# I.e. if bitstring is 1011, it initializes the qreg to 0100
def initialize_qureg_to_complement_of_bitstring(a_str, qreg, little_endian):
    a_n_str = conversion.get_negated_bistring(a_str)
    return initialize_qureg_given_bitstring(a_n_str, qreg, little_endian)


def initialize_qureg_to_complement_of_bitarray(a_arr, qreg, little_endian):
    a_n_str = conversion.get_negated_bitarray(a_arr)
    return initialize_qureg_given_bitstring(a_n_str, qreg, little_endian)


def initialize_qureg_to_complement_of_int(a_int, qreg, little_endian):
    a_str = conversion.get_bitstring_from_int(a_int, len(qreg))
    return initialize_qureg_to_complement_of_bitstring(a_str, qreg,
                                                       little_endian)
