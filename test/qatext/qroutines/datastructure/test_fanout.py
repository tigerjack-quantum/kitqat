from test.common_pytest import (REVERSIBLE_ON, REVERSIBLE_ON_REASON,
                                CircuitTestHelpers)

import pytest
from qat.lang.AQASM.program import Program
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import RSimulator
from qatext.qroutines.datastructure.fanout import fanout
from qatext.qroutines.qregs_mgmt.qregs_init import \
    initialize_qureg_given_bitstring


class TestFanout(CircuitTestHelpers):

    @pytest.mark.parametrize(
        "bitstring, n",
        [
            ("0",  1),
            ("1",  3),
            ("01",  2),
            ("10",  4),
            ("101",  3),
            ("111",  5),
            ("1010",  2),
            # useful for depth
            ("1101",  4),
            ("1101",  8),
            ("1101",  16),
            ("1101",  32),
        ],
    )
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_fanout(self, bitstring, n):
        m = len(bitstring)

        prw = ProgramWrapper(Program())
        # you can use int here instead of string just to show the potential of
        # inspect_state_reversible_program or get_rprogram_values
        qval = prw.qarray_alloc(1, m, "Original", str)
        qarray = prw.qarray_alloc(n, m, "Clones", str)

        prw.apply(initialize_qureg_given_bitstring(bitstring, False), qval)

        prw.apply(fanout(n, m), qval, qarray)
        name_to_values = RSimulator.simulate_and_decode(prw)
        # print(name_to_values)
        original = name_to_values.as_bitstring_list('Original')
        clones   = name_to_values.as_bitstring_list('Clones')
        assert original[0] == bitstring, "Original not correctly initialized %s" % original
        assert all(val == bitstring for val in clones), "Clones are not equal %s" % clones



