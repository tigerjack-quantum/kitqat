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


if __name__ == "__main__":
    pytest.main([__file__])
