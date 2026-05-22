# Author: Federico Pinto
import itertools

import galois
import pytest
from qat.lang.AQASM.program import Program

from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import get_states_from_program_wrapper
from qatext.qroutines.montgomery.Pinto_montgomery import (
    montgomery_form,
    montgomery_mult,
    montgomery_res,
)
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.utils.bits.conversion import get_int_from_bitarray


def montgomery_oracle_galois(x, y, p, n):
    """
    Classical oracle using the `galois` library.
    Calculates the Montgomery product in GF(p): x * y * 2^-n.
    """
    GF = galois.GF(p)
    xg = GF(x % p)
    yg = GF(y % p)

    two = GF(2)
    inv_two_n = two ** (-n)

    res = xg * yg * inv_two_n
    return int(res)


# Exhaustive test cases for p=13
EXHAUSTIVE_CASES_P13 = [(4, 13, a, b) for a, b in itertools.product(range(13), repeat=2)]

# Edge and random cases for larger moduli
EDGE_AND_RANDOM_CASES = [
    (6, 61, 60, 60),
    (6, 61, 60, 1),
    (8, 251, 250, 250),
    (8, 251, 125, 250),
    (6, 53, 42, 17),
    (8, 241, 111, 222),
]


class TestMontgomery:
    def _setup_and_run(self, val_a, val_b, n, p, gate, out_name):
        """Helper to set up and run a Montgomery circuit."""
        prw = ProgramWrapper(Program())

        qr_a = prw.qarray_alloc(1, n, "a", int)
        qr_b = prw.qarray_alloc(1, n, "b", int)
        qr_out = prw.qarray_alloc(1, n, out_name, int)

        prw.apply(qi.initialize_qureg_given_int(val_a, n, False), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, n, False), qr_b[0])

        prw.apply(gate, qr_a[0], qr_b[0], qr_out[0])

        res = get_states_from_program_wrapper(prw, [])
        return (
            get_int_from_bitarray(res["a"], False),
            get_int_from_bitarray(res["b"], False),
            get_int_from_bitarray(res[out_name], False),
        )

    @pytest.mark.parametrize("n, p, val_a, val_b", EXHAUSTIVE_CASES_P13 + EDGE_AND_RANDOM_CASES)
    def test_montgomery_mult_parametrized(self, n, p, val_a, val_b):
        """Test MONTGOMERY_MULT with final modular reduction."""
        gate = montgomery_mult(n, p)
        out_a, out_b, out_res = self._setup_and_run(val_a, val_b, n, p, gate, "res")

        expected_strict = montgomery_oracle_galois(val_a, val_b, p, n)

        assert out_res == expected_strict, (
            f"Computation error (n={n}, p={p}).\n"
            f"Input: {val_a} * {val_b} * 2^-{n} mod {p}\n"
            f"Expected (strict): {expected_strict}\n"
            f"Quantum Output: {out_res}"
        )

        assert 0 <= out_res < p, f"Output {out_res} not reduced in range [0, {p-1}]."
        assert out_a == val_a, f"Input A modified: {val_a} -> {out_a}"
        assert out_b == val_b, f"Input B modified: {val_b} -> {out_b}"

    def test_montgomery_form_and_res(self):
        """Test conversion to and from Montgomery form using galois oracles."""
        n = 6
        p = 53
        val = 42
        GF = galois.GF(p)

        # 1. To Montgomery form
        prw_form = ProgramWrapper(Program())
        qr_val = prw_form.qarray_alloc(1, n, "val", int)
        qr_form = prw_form.qarray_alloc(1, n, "form", int)

        prw_form.apply(qi.initialize_qureg_given_int(val, n, False), qr_val[0])
        prw_form.apply(montgomery_form(n, p), qr_val[0], qr_form[0])

        res_form = get_states_from_program_wrapper(prw_form, [])
        form_val = get_int_from_bitarray(res_form["form"], False)

        expected_form = int(GF(val % p) * (GF(2) ** n))

        assert form_val == expected_form, f"Form conversion error: got {form_val}, expected {expected_form}"

        # 2. Back from Montgomery form
        prw_res = ProgramWrapper(Program())
        qr_fval = prw_res.qarray_alloc(1, n, "fval", int)
        qr_orig = prw_res.qarray_alloc(1, n, "orig", int)

        prw_res.apply(qi.initialize_qureg_given_int(form_val, n, False), qr_fval[0])
        prw_res.apply(montgomery_res(n, p), qr_fval[0], qr_orig[0])

        res_orig = get_states_from_program_wrapper(prw_res, [])
        back_val = get_int_from_bitarray(res_orig["orig"], False)

        expected_back = int(GF(form_val % p) * (GF(2) ** (-n)))

        assert back_val == expected_back, f"Inverse conversion error: got {back_val}, expected {expected_back}"
        assert back_val == val % p, f"Logical consistency error: {back_val} != {val % p}"


if __name__ == "__main__":
    pytest.main([__file__])
