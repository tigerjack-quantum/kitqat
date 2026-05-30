from qatext.qpus.reversible import RSimulator
__author__ = "Federico Pinto <federico.pinto@mail.polimi.it>"
# Author: Federico Pinto
import pytest
import galois
from qat.lang.AQASM import Program, X
from qatext.qatmgmt.program import ProgramWrapper
from qatext.utils.bits.conversion import get_int_from_bitarray
from qatext.qroutines.algebraic.gfp.barret import q_c_mult_add, barrett_reduction, _get_const_add_gate
from qatext.qroutines.qregs_mgmt import qregs_init as qi


def test_q_c_mult_add():
    prw = ProgramWrapper(Program())
    qr_in = prw.qarray_alloc(1, 2, "in", int)
    qr_acc = prw.qarray_alloc(1, 4, "acc", int)
    prw.apply(X, qr_in[0][0])
    prw.apply(X, qr_in[0][1])
    q_c_mult_add(prw, qr_in[0], qr_acc[0], 2)
    res = RSimulator.simulate(prw, [])
    assert get_int_from_bitarray(res['acc'], False) == 6


@pytest.mark.parametrize("n, N, t_val", [
    (6, 53, 1000),
    (6, 53, 4000),
    (8, 251, 5000),
    (8, 251, 60000),
    # ---- Edge Cases ----
    (6, 53, 0),         # Zero
    (6, 53, 42),        # <  module
    (6, 53, 53),        # == module
    (6, 53, 4095),      # Max value 12-bit
    # ---- Prime Power Cases ----
    (6, 31, 2000),
    (6, 32, 2000),      # 2^5
])
def test_barrett_reduction_parametrized(n, N, t_val):
    # Mathematical oracle using galois library (strictly for Prime Power N)
    GF = galois.GF(N)
    expected_val = int(GF(t_val % N))

    prw = ProgramWrapper(Program())
    qr_t = prw.qarray_alloc(1, 2 * n, "t", int)
    qr_out = prw.qarray_alloc(1, n, "out", int)
    prw.apply(qi.initialize_qureg_given_int(t_val, 2 * n, False), qr_t[0])
    prw.apply(barrett_reduction(n, N), qr_t[0], qr_out[0])
    
    res = RSimulator.simulate(prw, [])
    out_val = get_int_from_bitarray(res['out'], False)
    
    assert out_val == expected_val, f"Error, epected {expected_val}, got {out_val}"

