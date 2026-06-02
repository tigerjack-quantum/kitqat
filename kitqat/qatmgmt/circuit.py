# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

from typing import Protocol, runtime_checkable, Optional, TYPE_CHECKING
from kitqat.qatmgmt.program import QArray
from kitqat.utils.bits.conversion import (get_bitstring_array,
                                          get_ints_from_bitarray)

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit

@runtime_checkable
class CircuitLike(Protocol):
    """Anything that can produce a Circuit and owns a name→QArray map.

    Both ProgramWrapper and QRoutineWrapper satisfy this contract.
    """

    _name_to_qarray: dict[str, QArray]

    def to_circ(self, *, link: Optional[list], inline: bool) -> "Circuit": ...
