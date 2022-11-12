import logging
from math import ceil, log
from typing import Any, Dict

from qat.lang.AQASM import SWAP, H, QRoutine, X
from qat.lang.AQASM.bits import QRegister
from qat.lang.AQASM.misc import build_gate

# if TYPE_CHECKING:
#     from qat.lang.AQASM import QRegister

logger = logging.getLogger(__name__)

# from typing_extension import TypedDict
# FpcPatternDict = TypedDict(
#     'FpcPatternDict', {
#         'n_lines': int,
#         'n_flips': int,
#         'negated_permutation': bool,
#         'swaps_pattern': List[Tuple[int, int, int]],
#         'to_negate_range': int,
#     })


def _common_checks(a_qs, flip_qs, benes_pattern_dict):
    assert len(a_qs) == benes_pattern_dict['n_lines']
    assert len(flip_qs) == benes_pattern_dict['n_flips']


# TODO switch to simple a_len and flip_len as input
# Using a special Dict[str, Any] as type for benes_pattern_dict causes problems with python3.6 multithread (pickle error)
@build_gate("BENES", [QRegister, QRegister, dict])
def generate(a_qs: 'QRegister', flip_qs: 'QRegister',
             benes_pattern_dict: Dict) -> QRoutine:
    a_len = len(a_qs)
    flip_len = len(flip_qs)
    routine = QRoutine(arity=a_len + flip_len)
    for i in range(a_len, a_len + flip_len):
        routine.apply(H, i)
    for i in range(benes_pattern_dict['to_negate_range']):
        routine.apply(X, i)
    for pattern in benes_pattern_dict['swaps_pattern']:
        # TODO change, but how
        # program.apply(SWAP.ctrl(), flip_qs[i[0]], a_qs[i[1]], a_qs[i[2]])
        routine.apply(SWAP.ctrl(), a_len + pattern[0], pattern[1], pattern[2])
    if benes_pattern_dict['negated_permutation']:
        # for i in range(benes_pattern_dict['to_negate_range']):
        for i in range(a_len):
            routine.apply(X, i)

    return routine


def get_generate_pattern(n, r) -> Dict[str, Any]:
    """Given how it's built, n should be a power of 2 and, if not, it returns
    the combination rounding up to the top power of 2. If the original n is not
    a power of 2, you may want to adapt the circuit avoiding the use of the
    last bits.

    Returns a dictionary containing the:
    1. n_lines, the number of lines required; it is the rounding up of n to a
    power of 2

    2. n_flips, the number of fair coin flips required to obtain the full
    permutation

    3. the swaps_pattern, i.e. a list of tuples containing:
    - an integer signalling which flip to use
    - the first line involved in the swap
    - the second line involved in the swap

    4. to_negate_range, i.e. which bits are initialized to 1 to apply the
    permutation pattern

    5. negated_permutation, a boolean signaling if the pattern is inversed;
    indeed, to reduce the number of flips, if r > (n/2), instead of
    initializing r bits to 1 and then apply the permutation network, we
    initialize n - r bits to 1 and apply the permutation network. In the latter
    case, the obtained permutation should be negated.
    """
    nwr_dict = {}
    steps = ceil(log(n, 2))
    nwr_dict['n_lines'] = 2**steps
    nwr_dict['swaps_pattern'] = []
    if (r == 0 or r == nwr_dict['n_lines']):
        raise ValueError("No permutation possible with r = {r}")

    # bcz ncr(8;5) == ncr(8;3)
    if r > nwr_dict['n_lines'] / 2:
        initial_swaps = nwr_dict['n_lines'] - r
    else:
        initial_swaps = r

    _get_generate_pattern_support(0, initial_swaps,
                                  int(nwr_dict['n_lines'] / 2), 0, nwr_dict)
    nwr_dict['n_flips'] = len(nwr_dict['swaps_pattern'])

    if (r > nwr_dict['n_lines'] / 2):
        nwr_dict['to_negate_range'] = nwr_dict['n_lines'] - r
        nwr_dict['negated_permutation'] = True
    else:
        nwr_dict['to_negate_range'] = r
        nwr_dict['negated_permutation'] = False
    return nwr_dict


def _get_generate_pattern_support(start, end, swap_step, flip_q_idx, nwr_dict):
    logger.debug("Start: %d, end: %d, swap_step: %d", start, end, swap_step)
    if (swap_step == 0 or start >= end):
        logger.debug("Base case recursion")
        return flip_q_idx

    for_iter = 0
    for i in range(start, end):
        for_iter += 1
        logger.info("cswap(%d, %d, %d)", flip_q_idx, i, i + swap_step)
        nwr_dict['swaps_pattern'].append((flip_q_idx, i, i + swap_step))
        flip_q_idx += 1

    for_iter_next = min(for_iter, int(swap_step / 2))
    logger.debug(
        "Before rec1, start: %d, end: %d, swap_step: %d, for_iter_next %d",
        start, end, swap_step, for_iter_next)
    flip_q_idx = _get_generate_pattern_support(start, start + for_iter_next,
                                               int(swap_step / 2), flip_q_idx,
                                               nwr_dict)
    logger.debug(
        "Before rec, start: %d, end: %d, swap_step: %d, for_iter_next %d",
        start, end, swap_step, for_iter_next)
    flip_q_idx = _get_generate_pattern_support(
        start + swap_step, start + swap_step + for_iter_next,
        int(swap_step / 2), flip_q_idx, nwr_dict)
    return flip_q_idx
