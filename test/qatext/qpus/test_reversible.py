"""Tests for RProgram and RSimulator.

Test organisation
-----------------
TestRGate          – unit tests for RProgram.apply (no circuits involved)
TestRProgramAlloc  – register allocation edge cases
TestFromCircuit    – RSimulator.from_circuit against hand-computed bitstrings
TestFromQRoutine   – apply_gates_from_qroutine
TestErrorHandling  – expected failures (non-reversible gates, bad args…)
TestQPUOracle      – slow integration tests that cross-check against QPU
                     (kept but clearly isolated; skipped when QPU unavailable)

The QPU is NOT used in the first five groups.  Instead we derive the expected
bitstring by one of three strategies depending on what is being tested:

  1. Hand-computed string  – for simple gate sequences the result is obvious.
  2. Reference RProgram    – apply the same logical operations to a bare
                             RProgram and compare.  This tests from_circuit
                             without trusting the QPU.
  3. Involution check      – applying a reversible circuit twice must return
                             to the initial state (self-inverse property).
"""
from __future__ import annotations

import pytest
from test.common_circuit import CircuitTestCase
from test.common_pytest import SLOW_TEST_ON, SLOW_TEST_ON_REASON

from qat.lang.AQASM.gates import CCNOT, SWAP, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.routines import QRoutine
from qatext.qpus.reversible import RGate, RProgram, RSimulator

# ---------------------------------------------------------------------------
# Shared gate factories (same as original test file)
# ---------------------------------------------------------------------------

@build_gate("MGATE1", [int], lambda x: x)
def _m_gate1(nbits: int) -> QRoutine:
    assert nbits > 1, f"{nbits}"
    qrout = QRoutine()
    qw = qrout.new_wires(nbits)
    for wire in qw[1:]:
        qrout.apply(X.ctrl(1), qw[0], wire)
    return qrout


@build_gate("MGATE2", [int], lambda x: x)
def _m_gate2(nbits: int) -> QRoutine:
    assert nbits > 3
    qrout = QRoutine()
    qw = qrout.new_wires(nbits)
    for i in range(1, len(qw) - 1):
        qrout.apply(SWAP.ctrl(), qw[0], qw[i], qw[i + 1])
    qrout2 = _m_gate1(nbits - 2)
    qrout.apply(qrout2, qw[0], qw[2], qw[4:])
    return qrout


def _m_gate3(nbits: int) -> QRoutine:
    assert nbits > 3
    qrout = QRoutine()
    qw = qrout.new_wires(nbits)
    for i in range(1, len(qw) - 1):
        qrout.apply(SWAP.ctrl(), qw[0], qw[i], qw[i + 1])
    qrout2 = _m_gate1.circuit_generator(nbits - 2)
    qrout.apply(qrout2, qw[0], qw[2], qw[4:])
    return qrout


# ---------------------------------------------------------------------------
# 1.  Unit tests for RProgram.apply  (no qat circuits)
# ---------------------------------------------------------------------------

class TestRGate(CircuitTestCase):
    N = 10

    def setUp(self):
        self.rpr = RProgram()
        self.rpr.ralloc(self.N)

    # -- NOT ------------------------------------------------------------------

    def test_not_single(self):
        self.rpr.apply(RGate.NOT, 3)
        self.assertEqual(self.rpr.get_result(), "0001000000"[::-1][::-1])
        expected = ["0"] * self.N
        expected[3] = "1"
        self.assertEqual(self.rpr.get_result(), "".join(expected))

    def test_not_multiple_targets_independent(self):
        for idx in (0, 4, 9):
            self.rpr.apply(RGate.NOT, idx)
        expected = ["0"] * self.N
        for idx in (0, 4, 9):
            expected[idx] = "1"
        self.assertEqual(self.rpr.get_result(), "".join(expected))

    def test_not_involution(self):
        """Applying NOT twice is identity."""
        self.rpr.apply(RGate.NOT, 5)
        self.rpr.apply(RGate.NOT, 5)
        self.assertEqual(self.rpr.get_result(), "0" * self.N)

    # -- SWAP -----------------------------------------------------------------

    def test_swap_basic(self):
        self.rpr.apply(RGate.NOT, 3)
        self.rpr.apply(RGate.SWAP, 3, 7)
        expected = ["0"] * self.N
        expected[7] = "1"
        self.assertEqual(self.rpr.get_result(), "".join(expected))

    def test_swap_involution(self):
        """SWAP twice is identity."""
        self.rpr.apply(RGate.NOT, 2)
        before = self.rpr.get_result()
        self.rpr.apply(RGate.SWAP, 2, 6)
        self.rpr.apply(RGate.SWAP, 2, 6)
        self.assertEqual(self.rpr.get_result(), before)

    def test_swap_both_set(self):
        self.rpr.apply(RGate.NOT, 1)
        self.rpr.apply(RGate.NOT, 2)
        self.rpr.apply(RGate.SWAP, 1, 2)
        expected = ["0"] * self.N
        expected[1] = "1"
        expected[2] = "1"
        self.assertEqual(self.rpr.get_result(), "".join(expected))

    # -- RESET ----------------------------------------------------------------

    def test_reset_clears_bit(self):
        self.rpr.apply(RGate.NOT, 4)
        self.rpr.apply(RGate.RESET, 4)
        self.assertEqual(self.rpr.get_result(), "0" * self.N)

    def test_reset_noop_on_zero(self):
        self.rpr.apply(RGate.RESET, 4)
        self.assertEqual(self.rpr.get_result(), "0" * self.N)

    # -- Controlled NOT -------------------------------------------------------

    def test_cnot_fires_when_ctrl_set(self):
        self.rpr.apply(RGate.NOT, 0)          # set control
        self.rpr.apply(RGate.NOT, 0, 5)       # CNOT: ctrl=0, tgt=5
        expected = ["0"] * self.N
        expected[0] = "1"
        expected[5] = "1"
        self.assertEqual(self.rpr.get_result(), "".join(expected))

    def test_cnot_blocked_when_ctrl_clear(self):
        self.rpr.apply(RGate.NOT, 0, 5)       # ctrl=0 is 0 → should not fire
        self.assertEqual(self.rpr.get_result(), "0" * self.N)

    def test_ccnot_fires_when_both_ctrls_set(self):
        self.rpr.apply(RGate.NOT, 0)
        self.rpr.apply(RGate.NOT, 1)
        self.rpr.apply(RGate.NOT, 0, 1, 9)   # CCNOT
        expected = ["0"] * self.N
        expected[0] = "1"
        expected[1] = "1"
        expected[9] = "1"
        self.assertEqual(self.rpr.get_result(), "".join(expected))

    def test_ccnot_blocked_when_one_ctrl_clear(self):
        self.rpr.apply(RGate.NOT, 0)           # only one control set
        self.rpr.apply(RGate.NOT, 0, 1, 9)
        expected = ["0"] * self.N
        expected[0] = "1"
        self.assertEqual(self.rpr.get_result(), "".join(expected))

    def test_mcmnot_many_controls(self):
        ctrls = [2, 5, 7]
        trgts = [1, 3, 4, 9]
        for i in ctrls:
            self.rpr.apply(RGate.NOT, i)
        for t in trgts:
            self.rpr.apply(RGate.NOT, *ctrls, t)
        expected = ["0"] * self.N
        for i in ctrls:
            expected[i] = "1"
        for i in trgts:
            expected[i] = "1"
        self.assertEqual(self.rpr.get_result(), "".join(expected))

    # -- Identity -------------------------------------------------------------

    def test_identity_gate(self):
        self.rpr.apply(RGate.NOT, 3)
        before = self.rpr.get_result()
        self.rpr.apply(RGate.I, 3)
        self.assertEqual(self.rpr.get_result(), before)


# ---------------------------------------------------------------------------
# 2.  Register allocation
# ---------------------------------------------------------------------------

class TestRProgramAlloc(CircuitTestCase):

    def test_single_ralloc(self):
        rpr = RProgram()
        rpr.ralloc(4, "reg")
        self.assertIn("reg", rpr.rregs)
        self.assertEqual(len(rpr.rbits), 4)

    def test_multiple_ralloc_no_overlap(self):
        rpr = RProgram()
        rpr.ralloc(3, "a")
        rpr.ralloc(4, "b")
        self.assertEqual(rpr.rregs["a"].slic, slice(0, 3))
        self.assertEqual(rpr.rregs["b"].slic, slice(3, 7))

    def test_duplicate_name_raises(self):
        rpr = RProgram()
        rpr.ralloc(2, "dup")
        with self.assertRaises(ValueError):
            rpr.ralloc(2, "dup")

    def test_unnamed_ralloc_gets_auto_name(self):
        rpr = RProgram()
        rpr.ralloc(3)
        self.assertEqual(len(rpr.rregs), 1)

    def test_filter_result_by_name(self):
        rpr = RProgram()
        rpr.ralloc(3, "x")
        rpr.ralloc(3, "y")
        rpr.apply(RGate.NOT, 0)   # flip first bit of "x"
        result = rpr.filter_result_by_name("x")
        self.assertIn("x", result)
        self.assertNotIn("y", result)
        self.assertEqual(result["x"].to01(), "100")


# ---------------------------------------------------------------------------
# 3.  RSimulator.from_circuit – hand-computed expected bitstrings
# ---------------------------------------------------------------------------

class TestFromCircuit(CircuitTestCase):
    """No QPU.  Expected values are derived analytically from the gate sequence."""

    def _sim(self, pr: Program, **kwargs) -> str:
        circ = pr.to_circ(**kwargs)
        return RSimulator.from_circuit(circ).get_result()

    # -- Basic gates ----------------------------------------------------------

    def test_single_x_gate(self):
        pr = Program()
        qr = pr.qalloc(4)
        pr.apply(X, qr[2])
        # bit 2 flipped:  0010
        self.assertEqual(self._sim(pr), "0010")

    def test_three_x_gates(self):
        pr = Program()
        qr = pr.qalloc(4)
        pr.apply(X, qr[0])
        pr.apply(X, qr[1])
        pr.apply(X, qr[3])
        self.assertEqual(self._sim(pr), "1101")

    def test_swap_gate(self):
        pr = Program()
        qr = pr.qalloc(4)
        pr.apply(X, qr[0])           # state: 1000
        pr.apply(SWAP, qr[0], qr[3])  # state: 0001
        self.assertEqual(self._sim(pr), "0001")

    def test_cnot_fires(self):
        pr = Program()
        qr = pr.qalloc(3)
        pr.apply(X, qr[0])            # ctrl set
        pr.apply(X.ctrl(), qr[0], qr[2])  # tgt flipped
        # state: 1 0 1
        self.assertEqual(self._sim(pr), "101")

    def test_cnot_blocked(self):
        pr = Program()
        qr = pr.qalloc(3)
        # ctrl (qr[0]) is 0 → CNOT does nothing
        pr.apply(X.ctrl(), qr[0], qr[2])
        self.assertEqual(self._sim(pr), "000")

    def test_ccnot_fires(self):
        pr = Program()
        qr = pr.qalloc(4)
        pr.apply(X, qr[0])
        pr.apply(X, qr[1])
        pr.apply(X, qr[2])
        pr.apply(CCNOT.ctrl(1), qr)   # ctrl on qr[0..2], tgt qr[3]
        # qr[0,1,2] all 1 → tgt flips
        self.assertEqual(self._sim(pr), "1111")

    def test_ccnot_blocked_partial_ctrls(self):
        pr = Program()
        qr = pr.qalloc(4)
        pr.apply(X, qr[0])
        pr.apply(X, qr[1])
        # qr[2] stays 0 → CCNOT with ctrl on all three does NOT fire
        pr.apply(CCNOT.ctrl(1), qr)
        self.assertEqual(self._sim(pr), "1100")

    # -- Involution property --------------------------------------------------

    def test_x_involution(self):
        """Applying X twice returns to |0>."""
        pr = Program()
        qr = pr.qalloc(5)
        for qb in qr:
            pr.apply(X, qb)
        for qb in qr:
            pr.apply(X, qb)
        self.assertEqual(self._sim(pr), "0" * 5)

    def test_swap_involution(self):
        pr = Program()
        qr = pr.qalloc(4)
        pr.apply(X, qr[0])
        pr.apply(SWAP, qr[0], qr[3])
        pr.apply(SWAP, qr[0], qr[3])
        self.assertEqual(self._sim(pr), "1000")

    def test_ccnot_involution(self):
        pr = Program()
        qr = pr.qalloc(3)
        pr.apply(X, qr[0])
        pr.apply(X, qr[1])
        pr.apply(CCNOT, qr[0], qr[1], qr[2])
        pr.apply(CCNOT, qr[0], qr[1], qr[2])
        # tgt flipped twice → back to 0
        self.assertEqual(self._sim(pr), "110")

    # -- Controlled gates not firing ------------------------------------------

    def test_controlled_swap_blocked(self):
        pr = Program()
        qr = pr.qalloc(3)
        pr.apply(X, qr[1])             # qr[1]=1, ctrl qr[0]=0
        pr.apply(SWAP.ctrl(), qr[0], qr[1], qr[2])
        # ctrl not set → SWAP does not fire → state unchanged
        self.assertEqual(self._sim(pr), "010")

    def test_controlled_swap_fires(self):
        pr = Program()
        qr = pr.qalloc(3)
        pr.apply(X, qr[0])             # ctrl set
        pr.apply(X, qr[1])             # qr[1]=1
        pr.apply(SWAP.ctrl(), qr[0], qr[1], qr[2])
        # ctrl fires → swap qr[1] and qr[2]: state 1 0 1
        self.assertEqual(self._sim(pr), "101")

    # -- Custom gates (reference RProgram strategy) ---------------------------

    def test_custom_gates_match_reference(self):
        """from_circuit matches a reference RProgram built with the same ops."""
        pr = Program()
        qr = pr.qalloc(5)
        pr.apply(X, qr[0])
        pr.apply(X, qr[4])
        pr.apply(SWAP, qr[4], qr[3])
        pr.apply(X.ctrl(), qr[0], qr[1])
        pr.apply(CCNOT, qr[:3])
        pr.apply(SWAP, qr[2], qr[4])
        pr.apply(SWAP.ctrl(3), qr)
        pr.apply(CCNOT, qr[2:5])
        pr.apply(SWAP.ctrl(3), qr)

        # Reference: replay the same ops on a bare RProgram
        ref = RProgram()
        ref.ralloc(5)
        ref.apply(RGate.NOT, 0)
        ref.apply(RGate.NOT, 4)
        ref.apply(RGate.SWAP, 4, 3)
        ref.apply(RGate.NOT, 0, 1)      # CNOT
        ref.apply(RGate.NOT, 0, 1, 2)   # CCNOT
        ref.apply(RGate.SWAP, 2, 4)
        # SWAP.ctrl(3) on [0,1,2,3,4]: ctrls=0,1,2 tgts=3,4 — but ctrl check
        # uses current state; replicate the same logic
        ref.apply(RGate.SWAP, 0, 1, 2, 3, 4)
        ref.apply(RGate.NOT, 2, 3, 4)   # CCNOT on qr[2:5]
        ref.apply(RGate.SWAP, 0, 1, 2, 3, 4)

        circ = pr.to_circ()
        result = RSimulator.from_circuit(circ).get_result()
        self.assertEqual(result, ref.get_result())

    def test_with_build_gates(self):
        # Involution: apply the same gate again and check we recover all-ones
        pr2 = Program()
        qr2 = pr2.qalloc(6)
        for qb in qr2:
            pr2.apply(X, qb)
        # print(RSimulator.inspect_program(pr2))
        # input()

        qfun_param2 = _m_gate2(4)
        pr2.apply(qfun_param2, qr2[1], qr2[3], qr2[4], qr2[2])
        pr2.apply(qfun_param2.dag(), qr2[1], qr2[3], qr2[4], qr2[2])
        # print(RSimulator.inspect_program(pr2))
        # input()

        circ2 = pr2.to_circ(include_matrices=False, submatrices_only=True)
        # print(RSimulator.inspect_circuit(circ2))
        # input()
        # After double application the result must equal the initial state
        self.assertEqual(RSimulator.from_circuit(circ2).get_result(), "1" * 6)

    def test_with_qroutines(self):
        # Double-apply involution check
        pr2 = Program()
        qr2 = pr2.qalloc(5)
        for qb in qr2:
            pr2.apply(X, qb)
        qfun2 = _m_gate3(4)
        pr2.apply(qfun2, qr2[1], qr2[0], qr2[4], qr2[2])
        pr2.apply(qfun2.dag(), qr2[1], qr2[0], qr2[4], qr2[2])
        circ2 = pr2.to_circ(include_matrices=False, submatrices_only=True)
        self.assertEqual(RSimulator.from_circuit(circ2).get_result(), "1" * 5)


# ---------------------------------------------------------------------------
# 4.  apply_gates_from_qroutine
# ---------------------------------------------------------------------------

class TestFromQRoutine(CircuitTestCase):
    N = 10

    def setUp(self):
        self.rcr = RProgram()
        self.rcr.ralloc(self.N)

    def _ref_from_program(self, pr: Program) -> str:
        circ = pr.to_circ()
        return RSimulator.from_circuit(circ).get_result()

    def test_qroutine_default_mapping(self):
        """apply_gates_from_qroutine with default identity mapping."""
        pr = Program()
        qr = pr.qalloc(self.N)
        for i, qb in enumerate(qr[:3]):
            pr.apply(X, qb)
            self.rcr.apply(RGate.NOT, i)
        qrout = _m_gate3(self.N)
        pr.apply(qrout, qr)
        self.rcr.apply_gates_from_qroutine(qrout)
        self.assertEqual(self.rcr.get_result(), self._ref_from_program(pr))

    def test_qroutine_custom_mapping(self):
        """apply_gates_from_qroutine with a non-trivial qubit remapping."""
        pr = Program()
        qr = pr.qalloc(self.N)
        for i, qb in enumerate(qr[:3]):
            pr.apply(X, qb)
            self.rcr.apply(RGate.NOT, i)
        tgt_qbits = qr[3:-2]
        qrout = _m_gate3(len(tgt_qbits))
        pr.apply(qrout, tgt_qbits)
        self.rcr.apply_gates_from_qroutine(qrout, [qb.index for qb in tgt_qbits])
        self.assertEqual(self.rcr.get_result(), self._ref_from_program(pr))

    def test_qroutine_involution(self):
        """Applying the same QRoutine twice returns to the starting state."""
        for i in range(3):
            self.rcr.apply(RGate.NOT, i)
        before = self.rcr.get_result()
        qrout = _m_gate3(self.N)
        self.rcr.apply_gates_from_qroutine(qrout)
        self.rcr.apply_gates_from_qroutine(qrout.dag())
        self.assertEqual(self.rcr.get_result(), before)

    def test_qroutine_too_few_qbits_raises(self):
        qrout = _m_gate3(self.N)
        with self.assertRaises(ValueError):
            self.rcr.apply_gates_from_qroutine(qrout, [0, 1])  # too few


# ---------------------------------------------------------------------------
# 5.  Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling(CircuitTestCase):

    def test_non_reversible_gate_raises(self):
        """H gate (non-reversible) must raise AttributeError."""
        from qat.lang.AQASM.gates import H
        pr = Program()
        pr.apply(H, pr.qalloc(1))
        circ = pr.to_circ()
        with self.assertRaises(AttributeError):
            RSimulator.from_circuit(circ)

    def test_apply_before_alloc_raises(self):
        rpr = RProgram()
        with self.assertRaises(AttributeError):
            rpr.apply(RGate.NOT, 0)

    def test_overlapping_ctrl_tgt_raises(self):
        rpr = RProgram()
        rpr.ralloc(5)
        rpr.apply(RGate.NOT, 3)
        with self.assertRaises(ValueError):
            rpr.apply(RGate.NOT, 4, 4)

    def test_duplicate_register_name_raises(self):
        rpr = RProgram()
        rpr.ralloc(3, "reg")
        with self.assertRaises(ValueError):
            rpr.ralloc(3, "reg")

    def test_unknown_gate_name_raises(self):
        rpr = RProgram()
        rpr.ralloc(4)
        with self.assertRaises(AttributeError):
            rpr._apply_gate_from_name("HADAMARD", [0])


# ---------------------------------------------------------------------------
# 6.  QPU integration tests  (slow; skipped when QPU not available)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not SLOW_TEST_ON, reason=SLOW_TEST_ON_REASON)

class TestQPUOracle(CircuitTestCase):
    """Cross-check RSimulator against a real QPU.

    These are integration tests — they are correct by design but slow.
    Run them explicitly to validate the simulator against the QPU oracle.
    """

    def _qpu_result(self, pr: Program, **to_circ_kwargs) -> str:
        circ = pr.to_circ(**to_circ_kwargs)
        res = self.qpu.submit(circ.to_job())
        sample = None
        for sample in res:
            pass
        assert sample is not None
        return sample.state.bitstring

    def test_controlled_ccnot(self):
        pr = Program()
        qr = pr.qalloc(4)
        pr.apply(X, qr[0])
        pr.apply(X, qr[1])
        pr.apply(X, qr[2])
        pr.apply(CCNOT.ctrl(1), qr)
        circ = pr.to_circ()
        self.assertEqual(
            self._qpu_result(pr),
            RSimulator.from_circuit(circ).get_result(),
        )

    def test_custom_gates(self):
        pr = Program()
        qr = pr.qalloc(5)
        pr.apply(X, qr[0])
        pr.apply(X, qr[4])
        pr.apply(SWAP, qr[4], qr[3])
        pr.apply(X.ctrl(), qr[0], qr[1])
        pr.apply(CCNOT, qr[:3])
        pr.apply(SWAP, qr[2], qr[4])
        pr.apply(SWAP.ctrl(3), qr)
        pr.apply(CCNOT, qr[2:5])
        pr.apply(SWAP.ctrl(3), qr)
        circ = pr.to_circ()
        self.assertEqual(
            self._qpu_result(pr),
            RSimulator.from_circuit(circ).get_result(),
        )

    def test_with_qroutines(self):
        pr = Program()
        qr = pr.qalloc(5)
        for qb in qr:
            pr.apply(X, qb)
        qfun = _m_gate3(4)
        pr.apply(qfun, qr[1], qr[0], qr[4], qr[2])
        circ = pr.to_circ(include_matrices=False, submatrices_only=True)
        self.assertEqual(
            self._qpu_result(pr, include_matrices=False, submatrices_only=True),
            RSimulator.from_circuit(circ).get_result(),
        )

    def test_with_build_gates(self):
        pr = Program()
        qr = pr.qalloc(6)
        for qb in qr:
            pr.apply(X, qb)
        qfun_param = _m_gate2(4)
        pr.apply(qfun_param, qr[1], qr[3], qr[4], qr[2])
        circ = pr.to_circ(include_matrices=False, submatrices_only=True)
        self.assertEqual(
            self._qpu_result(pr, include_matrices=False, submatrices_only=True),
            RSimulator.from_circuit(circ).get_result(),
        )
