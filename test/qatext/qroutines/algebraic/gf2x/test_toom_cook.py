from qatext.qpus.reversible import RSimulator
__author__ = "Federico Pinto <federico.pinto@mail.polimi.it>"
# Author: Federico Pinto
import random

import galois
import pytest
from qat.lang.AQASM.program import Program

from qatext.qatmgmt.program import ProgramWrapper
from qatext.qroutines.algebraic.gf2x.toom_cook import (
    karatsuba_modular,
    toom3_mult,
)
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.utils.bits.conversion import get_int_from_bitarray

random.seed(42)
random_n8_cases = [(random.randint(0, 255), random.randint(0, 255), 8, 283) for _ in range(20)]
random_n6_cases = [(random.randint(0, 63), random.randint(0, 63), 6) for _ in range(20)]


def galois_oracle_mul_mod(a_val, b_val, n, m_bits):
    """
    Polynomial multiplication modulo m(x) in GF(2^n) using galois extension fields.
    m_bits is an integer representing the irreducible polynomial.
    """
    GF = galois.GF(2**n, irreducible_poly=m_bits)
    res = GF(a_val) * GF(b_val)
    return int(res)


def galois_oracle_mul(a_val, b_val):
    """Standard integer multiplication oracle for Toom-Cook 3."""
    return a_val * b_val


class TestToomCook:
    def _setup_and_run(self, val_a, val_b, n, gate, out_size, out_name, little_endian):
        """Helper to reduce code duplication for circuit setup and execution."""
        prw = ProgramWrapper(Program())

        qr_a = prw.qarray_alloc(1, n, "a", int)
        qr_b = prw.qarray_alloc(1, n, "b", int)
        qr_out = prw.qarray_alloc(1, out_size, out_name, int)

        prw.apply(qi.initialize_qureg_given_int(val_a, n, little_endian), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, n, little_endian), qr_b[0])

        prw.apply(gate, qr_a[0], qr_b[0], qr_out[0])

        res = RSimulator.simulate(prw, [])
        return (
            get_int_from_bitarray(res["a"].tolist(), little_endian),
            get_int_from_bitarray(res["b"].tolist(), little_endian),
            get_int_from_bitarray(res[out_name].tolist(), little_endian),
        )

    def run_and_verify_karatsuba(self, val_a, val_b, n, m_bits):
        gate = karatsuba_modular(n, m_bits)
        out_a, out_b, out_h = self._setup_and_run(val_a, val_b, n, gate, n, "h", True)

        expected_h = galois_oracle_mul_mod(val_a, val_b, n, m_bits)

        assert out_h == expected_h, (
            f"Calculation error for n={n}, m_bits={m_bits}.\n"
            f"Input: {val_a} * {val_b}\n"
            f"Expected: {expected_h}, Got: {out_h}"
        )
        assert out_a == val_a, f"Initial: {val_a}, Final: {out_a}"
        assert out_b == val_b, f"Initial: {val_b}, Final: {out_b}"

    def run_and_verify_toom3(self, val_a, val_b, n):
        gate = toom3_mult(n)
        out_a, out_b, out_res = self._setup_and_run(val_a, val_b, n, gate, 2 * n, "out", False)

        expected_res = galois_oracle_mul(val_a, val_b)

        assert out_res == expected_res, (
            f"Calculation error for Toom-3 n={n}.\n"
            f"Input: {val_a} * {val_b}\n"
            f"Expected: {expected_res}, Got: {out_res}"
        )
        assert out_a == val_a, f"Initial: {val_a}, Final: {out_a}"
        assert out_b == val_b, f"Initial: {val_b}, Final: {out_b}"

    @pytest.mark.parametrize(
        "val_a, val_b, n, m_bits",
        [
            (0, 5, 4, 19),
            (5, 0, 4, 19),
            (1, 10, 4, 19),
            (10, 1, 4, 19),
            (2, 7, 4, 19),
            (15, 15, 4, 19),
            (0, 128, 8, 283),
            (1, 255, 8, 283),
            (255, 255, 8, 283),
            (2, 127, 8, 283),
        ]
        + random_n8_cases,
    )
    def test_karatsuba_modular_parametrized(self, val_a, val_b, n, m_bits):
        """Executes tests on edge cases and the random sample for n=8."""
        self.run_and_verify_karatsuba(val_a, val_b, n, m_bits)

    def test_karatsuba_n4(self):
        """Test for n=4: exhaustive combination testing."""
        n = 4
        m_bits = 19
        for a in range(16):
            for b in range(16):
                self.run_and_verify_karatsuba(a, b, n, m_bits)

    @pytest.mark.parametrize(
        "val_a, val_b, n",
        [
            (0, 5, 3),
            (5, 0, 3),
            (1, 7, 3),
            (7, 1, 3),
            (2, 5, 3),
            (7, 7, 3),
            (0, 32, 6),
            (1, 63, 6),
            (63, 63, 6),
            (2, 31, 6),
        ]
        + random_n6_cases,
    )
    def test_toom3_mult_parametrized(self, val_a, val_b, n):
        """Executes robust edge cases and random sampling tests for Toom-Cook 3."""
        self.run_and_verify_toom3(val_a, val_b, n)

    def test_toom3_n3(self):
        """Test for n=3: exhaustive combination testing."""
        n = 3
        for a in range(8):
            for b in range(8):
                self.run_and_verify_toom3(a, b, n)


if __name__ == "__main__":
    pytest.main([__file__])
