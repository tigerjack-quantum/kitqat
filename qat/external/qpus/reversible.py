"""For now it is only a test bench, creating a fake Program object.
 Virtually, it should be integrated into qat, taking a circuit as input and running the simulation.
"""
import logging
import operator
from enum import Enum, auto
from typing import Optional, Set, Union

from bitarray import bitarray

logger = logging.getLogger(__name__)


class ReversibleGate(Enum):
    NOT = auto()
    SWAP = auto()


class ReversibleQPU():

    def __init__(self):
        "docstring"
        self._ops = [
        ]  # should contain the list of operations for logging purposes
        self.qbits: Optional[bitarray] = None

    def qalloc(self, n=1):
        self.qbits = bitarray('0' * n)

    def apply(self, gate: ReversibleGate, ctrls: Optional[Set[int]],
              trgts: Union[int, Set[int]]):
        if self.qbits is None:
            raise AttributeError("You should initialize your qubits")
        # if len(trgts) == 0:
        #     return

        ctrl = ctrls is None or len(ctrls) == 0 or all(
            operator.itemgetter(*ctrls)(self.qbits))
        if not ctrl:
            return
        if isinstance(trgts, int):
            trgts = {trgts}
        if ctrls is not None and not ctrls.isdisjoint(trgts):
            raise ValueError("The target and control set should be disjoint")
        if gate == ReversibleGate.NOT:
            for trgt in trgts:
                self.qbits.invert(trgt)
        elif gate == ReversibleGate.SWAP:
            if len(trgts) == 2:
                _trgts = list(trgts)
                self.qbits[_trgts[1]], self.qbits[_trgts[0]] = self.qbits[
                    _trgts[0]], self.qbits[_trgts[1]]
            else:
                raise ValueError("Swap gates can have only 2 targets")
        else:
            raise ValueError(f"Unknown gate {gate}")
