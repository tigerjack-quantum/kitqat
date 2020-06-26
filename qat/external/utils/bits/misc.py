# DONE
import logging
from math import ceil, log

logger = logging.getLogger(__name__)


def check_enough_bits(a_int: int, bits: int):
    bits_required = get_required_bits(a_int)
    assert bits >= bits_required, "Not enough bits."


def get_required_bits(*ints: int) -> int:
    if len(ints) == 0:
        raise Exception("number of ints must be greater than 0")
    if len(ints) == 1:
        to_check_int = ints[0]
    else:
        maxi = abs(max(ints))
        mini = abs(min(ints))
        to_check_int = max(maxi, mini)
    bits_required = ceil(log(to_check_int + 1, 2))
    if bits_required == 0:
        return 1
    return bits_required
