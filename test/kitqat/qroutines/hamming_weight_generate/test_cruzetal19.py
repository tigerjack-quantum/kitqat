from itertools import chain

from test.common_pytest import (SLOW_TEST_ON, SLOW_TEST_ON_REASON,
                                CircuitTestHelpers)
from typing import TYPE_CHECKING
from kitqat.qroutines.hamming_weight_generate.cruzetal19 import w_state

import pytest
from qat.lang.AQASM.program import Program
from kitqat.qatmgmt.program import ProgramWrapper

if TYPE_CHECKING:
    from kitqat.qatmgmt.program import QArray


# @pytest.mark.usefixtures("setup_simulator", "setup_logger")
class TestCruzetal19(CircuitTestHelpers):

    def _test_common(self, n: int):
        prog = Program()
        qbits = prog.qalloc(n)
        prog.apply(w_state(n), qbits)
        circ = prog.to_circ()
        # circ = w_state_log_depth(n)
        print(circ.statistics())
        print("depth = ", circ.depth(default=1))

        result = self.simulate_circuit(circ)
        expected_prob = 1/n
        for sample in result:
            state_int = int(sample.state.state)
            # The trick x & (x-1) == 0 is the standard bit-twiddling check for
            # "power of two" (i.e. exactly one bit set)
            assert state_int != 0 and (state_int & (state_int - 1)) == 0, \
                f"State {sample.state} is not a weight-1 bitstring!"
            assert abs(sample.probability - expected_prob) < 1e-6, \
                f"State {sample.state} has prob {sample.probability:.6f}, expected {1/n:.6f}"

    @pytest.mark.parametrize("n", [2, 3, 4, 6, 8, 16, 24])
    def test_wstate(self, n):
        self._test_common(n)

    # @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
