import logging
from typing import List

LOGGER = logging.getLogger(__name__)


# WARN: Returns 2's complement. If you want the negation of the bitstring
# representing i, you can use this method followed by the get_negated_bitstring
def get_bitstring_from_int(i: int, max_bits: int, littleEndian=False) -> str:
    if i >= 0:
        bitstr = bin(i)[2:].zfill(max_bits)
    else:
        bitstr = bin(2**max_bits + i)[2:].zfill(max_bits)
    if len(bitstr) > max_bits:
        raise ValueError("more than max_bits")
    return bitstr if not littleEndian else bitstr[::-1]


def get_bitarray_from_int(i: int,
                          max_bits: int,
                          littleEndian=False) -> List[int]:
    return [int(x) for x in get_bitstring_from_int(i, max_bits, littleEndian)]


def get_negated_bistring(a_str: str) -> str:
    return a_str.translate(str.maketrans("01", "10"))
    # Map seems to be slower
    # return list(map(lambda x: 1 if int(x) == 0 else (0 if int(x) == 1 else
    # None), ss))


def get_negated_bitarray(a_arr: List[int]) -> List[int]:
    return [1 if int(x) == 0 else 0 for x in a_arr]

def get_ints_from_bitarray(state_arr: List[int],
                            n: int,
                            m: int,
                            littleEndian=False) -> tuple[int]:
    return get_ints_from_bitstring("".join(str(e) for e in state_arr), n, m, littleEndian)

def get_ints_from_bitstring(state_str: str,
                            n: int,
                            m: int,
                            littleEndian=False) -> tuple[int]:
    """Given a bitstring, extract the corresponding integers. The bitstring is
    assumed to contain n integers, represented on m qubits."""
    ons = []
    for i in range(n):
        slice_ = state_str[i * m:(i + 1) * m]
        if not slice_:
            raise ValueError(
                f"Empty slice for i={i}, m={m}, state_str='{state_str}'")
        ons.append(get_int_from_bitstring(slice_, littleEndian))
    return tuple(ons)


def get_int_from_bitstring(a_str: str, littleEndian=False) -> int:
    return int(a_str if not littleEndian else a_str[::-1], 2)


def get_int_from_bitarray(a_arr: List[int], littleEndian=False) -> int:
    return get_int_from_bitstring("".join(str(e) for e in a_arr), littleEndian)
