import galois
import pytest
from qat.lang.AQASM.program import Program

from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import get_states_from_program_wrapper
from qatext.qroutines.algebraic.gf2x.Pinto_basic_arith import (
    adder_n_bit,
    adder2bit,
    mul_n_bit,
    mul2bit,
    sub2bit,
    schoolbook_reduction,
    schoolbook_reduction_int,
)
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.utils.bits.conversion import get_int_from_bitarray


class TestPintoBasicArith:
    @pytest.mark.parametrize(
        "val_a, val_b",
        [
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
        ],
    )
    def test_adder2bit(self, val_a, val_b):
        prw = ProgramWrapper(Program())
        qr_a = prw.qarray_alloc(1, 1, "a", int)
        qr_b = prw.qarray_alloc(1, 1, "b", int)

        prw.apply(qi.initialize_qureg_given_int(val_a, 1, False), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, 1, False), qr_b[0])

        prw.apply(adder2bit(), qr_a[0], qr_b[0])

        res = get_states_from_program_wrapper(prw, [])

        out_a = get_int_from_bitarray(res["a"], False)
        out_b = get_int_from_bitarray(res["b"], False)

        GF2 = galois.GF(2)
        expected_b = int(GF2(val_a) + GF2(val_b))

        assert out_a == val_a
        assert out_b == expected_b, f"Calculation error: {val_a} + {val_b} in GF(2) is {expected_b}, not {out_b}"

    def test_sub2bit_alias(self):
        """A quick test to verify that the sub2bit alias works exactly like adder2bit."""
        prw = ProgramWrapper(Program())
        qr_a = prw.qarray_alloc(1, 1, "a", int)
        qr_b = prw.qarray_alloc(1, 1, "b", int)

        prw.apply(qi.initialize_qureg_given_int(1, 1, False), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(1, 1, False), qr_b[0])

        prw.apply(sub2bit(), qr_a[0], qr_b[0])

        res = get_states_from_program_wrapper(prw, [])
        out_b = get_int_from_bitarray(res["b"], False)

        GF2 = galois.GF(2)
        assert out_b == int(GF2(1) - GF2(1)), f"Subtractor failed, 1-1 should be 0, not {out_b}"

    @pytest.mark.parametrize(
        "val_a, val_b",
        [
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
        ],
    )
    def test_mul2bit(self, val_a, val_b):
        prw = ProgramWrapper(Program())
        qr_a = prw.qarray_alloc(1, 1, "a", int)
        qr_b = prw.qarray_alloc(1, 1, "b", int)
        qr_out = prw.qarray_alloc(1, 1, "out", int)

        prw.apply(qi.initialize_qureg_given_int(val_a, 1, False), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, 1, False), qr_b[0])

        prw.apply(mul2bit(), qr_a[0], qr_b[0], qr_out[0])

        res = get_states_from_program_wrapper(prw, [])

        out_a = get_int_from_bitarray(res["a"], False)
        out_b = get_int_from_bitarray(res["b"], False)
        final_out = get_int_from_bitarray(res["out"], False)

        GF2 = galois.GF(2)
        expected_out = int(GF2(val_a) * GF2(val_b))

        assert out_a == val_a
        assert out_b == val_b
        assert final_out == expected_out, f"Error: {val_a} * {val_b} is {expected_out}, not {final_out}"

    @pytest.mark.parametrize(
        "val_a, val_b, nbits",
        [
            (1, 1, 1),
            (0, 3, 2),
            (2, 3, 2),
            (3, 3, 2),
            (0, 7, 3),
            (5, 3, 3),
            (7, 7, 3),
            (2, 5, 3),
        ],
    )
    def test_adder_n_bit(self, val_a, val_b, nbits):
        """Test the N-bit adder for polynomials with edge cases up to 3 bits."""
        prw = ProgramWrapper(Program())

        qr_a = prw.qarray_alloc(1, nbits, "a", int)
        qr_b = prw.qarray_alloc(1, nbits, "b", int)

        prw.apply(qi.initialize_qureg_given_int(val_a, nbits, False), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, nbits, False), qr_b[0])

        prw.apply(adder_n_bit(nbits), qr_a[0], qr_b[0])

        res = get_states_from_program_wrapper(prw, [])

        out_a = get_int_from_bitarray(res["a"], False)
        out_b = get_int_from_bitarray(res["b"], False)

        poly_a = galois.Poly.Int(val_a, field=galois.GF(2))
        poly_b = galois.Poly.Int(val_b, field=galois.GF(2))
        expected_b = int(poly_a + poly_b)

        assert out_a == val_a
        assert out_b == expected_b, f"Error with {nbits} bits: {val_a} + {val_b} should be {expected_b}, but got {out_b}"

    @pytest.mark.parametrize(
        "val_a, val_b, nbits",
        [
            (1, 1, 1),
            (0, 3, 2),
            (1, 3, 2),
            (2, 2, 2),
            (3, 3, 2),
            (7, 3, 3),
            (5, 5, 3),
            (6, 7, 3),
        ],
    )
    def test_mul_n_bit(self, val_a, val_b, nbits):
        """Test the N-bit multiplication in GF(2^m)."""
        prw = ProgramWrapper(Program())

        qr_a = prw.qarray_alloc(1, nbits, "a", int)
        qr_b = prw.qarray_alloc(1, nbits, "b", int)
        qr_out = prw.qarray_alloc(1, nbits * 2, "out", int)

        prw.apply(qi.initialize_qureg_given_int(val_a, nbits, True), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, nbits, True), qr_b[0])

        prw.apply(mul_n_bit(nbits), qr_a[0], qr_b[0], qr_out[0])

        res = get_states_from_program_wrapper(prw, [])

        out_a = get_int_from_bitarray(res["a"], True)
        out_b = get_int_from_bitarray(res["b"], True)
        final_out = get_int_from_bitarray(res["out"], True)

        poly_a = galois.Poly.Int(val_a, field=galois.GF(2))
        poly_b = galois.Poly.Int(val_b, field=galois.GF(2))
        expected_out = int(poly_a * poly_b)

        assert out_a == val_a
        assert out_b == val_b
        assert final_out == expected_out, f"Multiplication error: {val_a} * {val_b} should be {expected_out}, but got {final_out}"

    @pytest.mark.parametrize(
        "val, mod, nbits",
        [
            (0b1011, 0b101, 2), # 11 mod 5 -> n=2, modulus has degree 2
            (0b1000, 0b111, 2), # x^3 mod (x^2+x+1) -> 8 mod 7
            (0b11010, 0b1011, 3), # x^4+x^3+x mod x^3+x+1 -> 26 mod 11 = 7, quot 3
            (0b110111, 0b1001, 3), # 55 mod 9 (x^3+1)
        ],
    )
    def test_schoolbook_reduction(self, val, mod, nbits):
        prw = ProgramWrapper(Program())
        qr = prw.qarray_alloc(1, 2 * nbits, "reg", int)

        prw.apply(qi.initialize_qureg_given_int(val, 2 * nbits, True), qr[0])
        prw.apply(schoolbook_reduction(nbits, mod), qr[0])

        res = get_states_from_program_wrapper(prw, [])

        out_val = get_int_from_bitarray(res["reg"], True)

        poly_val = galois.Poly.Int(val, field=galois.GF(2))
        poly_mod = galois.Poly.Int(mod, field=galois.GF(2))

        expected_rem = int(poly_val % poly_mod)
        expected_quot = int(poly_val // poly_mod)

        # remainder is in lower n bits, quotient in upper n bits
        expected_out = (expected_quot << nbits) | expected_rem

        assert out_val == expected_out, f"Reduction error: {val} % {mod} should be {expected_rem} with quotient {expected_quot}, got {out_val}"

    @pytest.mark.parametrize(
        "val, N, n",
        [
            (10, 3, 2), # 10 mod 3 = 1
            (25, 7, 3), # 25 mod 7 = 4
            (50, 11, 4), # 50 mod 11 = 6
            (100, 13, 4), # 100 mod 13 = 9
        ],
    )
    def test_schoolbook_reduction_int(self, val, N, n):
        prw = ProgramWrapper(Program())
        qr = prw.qarray_alloc(1, 2 * n, "reg", int)
        r_qr = prw.qarray_alloc(1, n + 1, "quotient", int)
        
        prw.apply(qi.initialize_qureg_given_int(val, 2 * n, False), qr[0])
        
        prw.apply(schoolbook_reduction_int(n, N), qr[0], r_qr[0])
        
        res = get_states_from_program_wrapper(prw, [])
        
       
        out_val = get_int_from_bitarray(res["reg"], False)
        
        expected_rem = val % N
        assert out_val == expected_rem, f"Integer reduction error: {val} % {N} should be {expected_rem}, but got {out_val}"
if __name__ == "__main__":
    pytest.main([__file__])
