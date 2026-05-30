__authors__ = [
    "Federico Pinto <federico.pinto@mail.polimi.it>",
    "Simone Perriello <sperriello@proton.me>",
]
import pytest
from qat.lang.AQASM.program import Program
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import RSimulator
from qatext.qroutines.algebraic.gfp.kaliski_inversion import mk_round
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.utils.bits.conversion import get_int_from_bitarray


class TestKaliskiInversion:
    @pytest.mark.parametrize(
        "val_u, val_v, val_r, val_s, nbits",
        [
            # --- 1. COPERTURA RAMI PRINCIPALI (nbits = 4) ---
            (10, 7, 1, 2, 4),  # Branch 1: u è pari -> u >>= 1, s <<= 1
            (11, 8, 0, 1, 4),  # Branch 2: u è dispari, v è pari -> v >>= 1, r <<= 1
            (11, 7, 0, 1, 4),  # Branch 3: u, v dispari, u > v -> u=(u-v)>>1, r=r+s, s<<=1
            (5, 7, 1, 2, 4),   # Branch 4a: u, v dispari, u < v -> v=(v-u)>>1, s=r+s, r<<=1

            # --- 2. EDGE CASES (Casi limite e Uguaglianza, nbits = 4) ---
            (7, 7, 1, 1, 4),   # Branch 4b: u == v (dispari). Dovrebbe azzerare v.
            (0, 5, 1, 1, 4),   # u è zero (condizione estrema del pari)
            (5, 0, 1, 1, 4),   # v è zero (con u dispari)
            (0, 0, 0, 0, 4),   # Zero assoluto su tutti i fronti
            (15, 15, 2, 2, 4), # Valori massimi assoluti per 4 bit (15 è 1111 in binario)
            (15, 14, 1, 1, 4), # u massimo (dispari), v massimo pari (14 è 1110)

            # --- 3. STRESS TEST SCALABILITÀ (nbits = 2) ---
            # Verifica che il circuito non si rompa con registri piccolissimi
            (3, 2, 1, 0, 2),   # u=3 (dispari), v=2 (pari)
            (2, 3, 0, 1, 2),   # u=2 (pari), v=3 (dispari)
            (3, 3, 1, 1, 2),   # u == v massimi per 2 bit

            # --- 4. STRESS TEST SCALABILITÀ (nbits = 8) ---
            # Verifica che il routing dei qubit e i carry non vadano in overflow con byte interi
            (255, 127, 5, 10, 8), # u > v, valori alti
            (127, 255, 10, 5, 8), # u < v, valori alti
            (128, 255, 1, 1, 8),  # u pari (limite potenza di 2), v dispari
        ],
    )
    def test_mk_round(self, val_u, val_v, val_r, val_s, nbits):
        prw = ProgramWrapper(Program())
        qr_u = prw.qarray_alloc(1, nbits, "u", int)
        qr_v = prw.qarray_alloc(1, nbits, "v", int)
        qr_r = prw.qarray_alloc(1, nbits + 1, "r", int)
        qr_s = prw.qarray_alloc(1, nbits + 1, "s", int)
        qr_k = prw.qarray_alloc(1, nbits, "k", int)
        qr_f = prw.qarray_alloc(1, 1, "f", int)
        qr_m = prw.qarray_alloc(1, 1, "m_i", int)

        prw.apply(qi.initialize_qureg_given_int(val_u, nbits, False), qr_u[0])
        prw.apply(qi.initialize_qureg_given_int(val_v, nbits, False), qr_v[0])
        prw.apply(qi.initialize_qureg_given_int(val_r, nbits + 1, False), qr_r[0])
        prw.apply(qi.initialize_qureg_given_int(val_s, nbits + 1, False), qr_s[0])
        prw.apply(qi.initialize_qureg_given_int(0, nbits, False), qr_k[0])
        prw.apply(qi.initialize_qureg_given_int(1, 1, False), qr_f[0])
        prw.apply(qi.initialize_qureg_given_int(0, 1, False), qr_m[0])

        prw.apply(mk_round(nbits), qr_u[0], qr_v[0], qr_r[0], qr_s[0], qr_k[0], qr_f[0], qr_m[0])

        res = RSimulator.simulate(prw, [])
        out_u = get_int_from_bitarray(res["u"].tolist(), False)
        out_v = get_int_from_bitarray(res["v"].tolist(), False)
        out_r = get_int_from_bitarray(res["r"].tolist(), False)
        out_s = get_int_from_bitarray(res["s"].tolist(), False)
        out_m = get_int_from_bitarray(res["m_i"].tolist(), False)

        expected_u, expected_v, expected_r, expected_s = val_u, val_v, val_r, val_s
        expected_m = 0
        if val_u % 2 == 0:
            expected_u >>= 1
            expected_s <<= 1
        elif val_v % 2 == 0:
            expected_v >>= 1
            expected_r <<= 1
            expected_m = 1
        elif val_u > val_v:
            expected_u = (val_u - val_v) >> 1
            expected_r = val_r + val_s
            expected_s <<= 1
            expected_m = 1
        else:
            expected_v = (val_v - val_u) >> 1
            expected_s = val_r + val_s
            expected_r <<= 1

        assert out_u == expected_u, f"u: got {out_u}, expected {expected_u}"
        assert out_v == expected_v, f"v: got {out_v}, expected {expected_v}"
        assert out_r == expected_r, f"r: got {out_r}, expected {expected_r}"
        assert out_s == expected_s, f"s: got {out_s}, expected {expected_s}"
        assert out_m == expected_m, f"m_i: got {out_m}, expected {expected_m}"
