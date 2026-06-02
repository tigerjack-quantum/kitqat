from test.common_pytest import (REVERSIBLE_ON, REVERSIBLE_ON_REASON,
                                CircuitTestHelpers)
from typing import Sequence

import pytest
from kitqat.qatmgmt.program import ProgramWrapper
from kitqat.qpus.reversible import RSimulator
from kitqat.qroutines.arith import perriello_arith
from kitqat.qroutines.qregs_mgmt import qregs_init as qregs
from qat.lang.AQASM.program import Program


class TestPerrielloArith(CircuitTestHelpers):

    @pytest.mark.parametrize("a_int, b_int", [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ])
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_two_bits_adder(self, a_int, b_int):
        """Add a_int and b_int and check their result.

        The number of bits used to represent the ints is computed at
        runtime.
        """
        self.prw = ProgramWrapper(Program())
        self.a = self.prw.qarray_alloc(1, 1, "a", int)
        self.b = self.prw.qarray_alloc(1, 2, "b", int)
        qfun = qregs.initialize_qureg_given_int(a_int, len(self.a), True)
        self.prw.apply(qfun, self.a)
        qfun = qregs.initialize_qureg_given_int(b_int, len(self.b), True)
        self.prw.apply(qfun, self.b[0][0])

        self.prw.apply(perriello_arith.two_bit_adder(True, True), self.a,
                       self.b)
        name_to_values = RSimulator.simulate_and_decode(self.prw)
        expected = a_int + b_int
        res_b = name_to_values['b']
        assert isinstance(res_b, Sequence)
        assert len(res_b) == 1
        assert res_b[0] == expected

    @pytest.mark.parametrize("a_int, b_int", [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ])
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_two_bits_comparator(self, a_int, b_int):
        """Add a_int and b_int and check their result.

        The number of bits used to represent the ints is computed at
        runtime.
        """
        # bits = misc.get_required_bits(a_int, b_int)
        self.prw = ProgramWrapper(Program())
        self.a = self.prw.qarray_alloc(1, 1, "a", int)
        self.b = self.prw.qarray_alloc(1, 1, "b", int)
        self.c = self.prw.qarray_alloc(1, 1, "c", int)

        qfun = qregs.initialize_qureg_given_int(a_int, len(self.a), True)
        self.prw.apply(qfun, self.a)
        qfun = qregs.initialize_qureg_given_int(b_int, len(self.b), True)
        self.prw.apply(qfun, self.b)

        self.prw.apply(perriello_arith.two_bit_comparator(), self.a, self.b,
                       self.c)

        name_to_values = RSimulator.simulate_and_decode(self.prw)
        res_c = name_to_values['c']
        assert isinstance(res_c, Sequence)
        assert len(res_c) == 1
        expected = int(a_int > b_int)
        assert res_c[0] == expected
