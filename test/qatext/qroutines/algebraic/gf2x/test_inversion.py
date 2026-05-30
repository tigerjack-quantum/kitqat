__authors__ = [
    "Federico Pinto <federico.pinto@mail.polimi.it>",
    "Simone Perriello <sperriello@proton.me>",
]

import galois
import pytest
from qat.lang.AQASM.program import Program
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import RSimulator
from qatext.qroutines.algebraic.gf2x.inversion import (flt_div, modmult,
                                                       square_mod)
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.utils.bits.conversion import get_int_from_bitarray


class TestInversion:
    @pytest.mark.parametrize(
        "val, mod, nbits",
        [
            (0b010, 0b1011, 3), # x mod (x^3+x+1), val=2, mod=11
            (0b110, 0b1011, 3), # x^2+x mod (x^3+x+1), val=6
        ],
    )
    def test_square_mod(self, val, mod, nbits):
        prw = ProgramWrapper(Program())
        qr_in = prw.qarray_alloc(1, nbits, "reg_in", int)
        qr_out = prw.qarray_alloc(1, nbits, "reg_out", int)

        prw.apply(qi.initialize_qureg_given_int(val, nbits, True), qr_in[0])

        prw.apply(square_mod(nbits, mod), qr_in[0], qr_out[0])

        res = RSimulator.simulate(prw, [])
        out_val = get_int_from_bitarray(res["reg_out"].tolist(), True)

        poly_val = galois.Poly.Int(val, field=galois.GF(2))
        poly_mod = galois.Poly.Int(mod, field=galois.GF(2))
        expected_out = int((poly_val ** 2) % poly_mod)

        assert out_val == expected_out, f"Error: {val}^2 mod {mod} should be {expected_out}, got {out_val}"

    @pytest.mark.parametrize(
        "val_a, val_b, val_c, mod, nbits",
        [
            (0b010, 0b011, 0b001, 0b1011, 3), # 2 * 3 + 1 mod 11 = 7 mod 11
            (0b110, 0b101, 0b010, 0b1011, 3), # 6 * 5 + 2 mod 11
        ],
    )
    def test_modmult(self, val_a, val_b, val_c, mod, nbits):
        prw = ProgramWrapper(Program())
        qr_a = prw.qarray_alloc(1, nbits, "reg_a", int)
        qr_b = prw.qarray_alloc(1, nbits, "reg_b", int)
        qr_c = prw.qarray_alloc(1, nbits, "reg_c", int)

        prw.apply(qi.initialize_qureg_given_int(val_a, nbits, True), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, nbits, True), qr_b[0])
        prw.apply(qi.initialize_qureg_given_int(val_c, nbits, True), qr_c[0])

        prw.apply(modmult(nbits, mod), qr_a[0], qr_b[0], qr_c[0])

        res = RSimulator.simulate(prw, [])
        out_val = get_int_from_bitarray(res["reg_c"].tolist(), True)

        poly_a = galois.Poly.Int(val_a, field=galois.GF(2))
        poly_b = galois.Poly.Int(val_b, field=galois.GF(2))
        poly_c = galois.Poly.Int(val_c, field=galois.GF(2))
        poly_mod = galois.Poly.Int(mod, field=galois.GF(2))

        expected_out = int((poly_c + poly_a * poly_b) % poly_mod)

        assert out_val == expected_out, f"Error: {val_c} + {val_a}*{val_b} mod {mod} should be {expected_out}, got {out_val}"

    @pytest.mark.parametrize(
        "val_f, val_b, mod, nbits",
        [
            (0b010, 0b011, 0b1011, 3), # f=2, b=3, mod=11 (GF(2^3) with x^3+x+1). Inverse of 2 is x^2+1 = 5.
            (0b110, 0b101, 0b1011, 3), # f=6, b=5
            (0b001, 0b110, 0b1011, 3), # inverse of 1 is 1
        ],
    )
    def test_flt_div(self, val_f, val_b, mod, nbits):
        prw = ProgramWrapper(Program())
        qr_f0 = prw.qarray_alloc(1, nbits, "reg_f0", int)
        qr_b = prw.qarray_alloc(1, nbits, "reg_b", int)
        qr_c = prw.qarray_alloc(1, nbits, "reg_c", int)

        prw.apply(qi.initialize_qureg_given_int(val_f, nbits, True), qr_f0[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, nbits, True), qr_b[0])

        prw.apply(flt_div(nbits, mod), qr_f0[0], qr_b[0], qr_c[0])

        res = RSimulator.simulate(prw, [])
        out_c = get_int_from_bitarray(res["reg_c"].tolist(), True)

        # poly_f = galois.Poly.Int(val_f, field=galois.GF(2))
        # poly_b = galois.Poly.Int(val_b, field=galois.GF(2))
        poly_mod = galois.Poly.Int(mod, field=galois.GF(2))

        GF = galois.GF(2**nbits, irreducible_poly=poly_mod)
        gf_f = GF(val_f)
        gf_b = GF(val_b)

        if val_f == 0:
            expected_out = 0
        else:
            expected_out = int(gf_b / gf_f)

        assert out_c == expected_out, f"Error: {val_b} / {val_f} mod {mod} should be {expected_out}, got {out_c}"


