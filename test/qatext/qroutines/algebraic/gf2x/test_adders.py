__author__ = "Federico Pinto <federico.pinto@mail.polimi.it>"
# Author: Federico Pinto
# -*- coding: utf-8 -*-
import pytest
import random
from qat.lang.AQASM.program import Program
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import get_states_from_program_wrapper
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.utils.bits.conversion import get_int_from_bitarray
from qatext.qroutines.algebraic.gf2x.adders import cuccaro_adder_int, tkk_adder_int

random.seed(42)

# Test cases: (a_val, b_val, a_len, b_len)
random_cases = []
for _ in range(20):
    al = random.randint(2, 6)
    bl = random.randint(2, 6)
    a = random.randint(0, (1 << al) - 1)
    b = random.randint(0, (1 << bl) - 1)
    random_cases.append((a, b, al, bl))

class TestPintoAdders:
    
    def _setup_and_run(self, val_a, val_b, a_len, b_len, gate, overflow, little_endian=False):
        """Helper to reduce code duplication for circuit setup and execution."""
        prw = ProgramWrapper(Program())
        
        qr_a = prw.qarray_alloc(1, a_len, "a", int)
        qr_b = prw.qarray_alloc(1, b_len, "b", int)
        
        if overflow:
            qr_cout = prw.qarray_alloc(1, 1, "cout", int)
        
        prw.apply(qi.initialize_qureg_given_int(val_a, a_len, little_endian), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, b_len, little_endian), qr_b[0])
        
        if overflow:
            prw.apply(gate, qr_a[0], qr_b[0], qr_cout[0])
        else:
            prw.apply(gate, qr_a[0], qr_b[0])
        
        res = get_states_from_program_wrapper(prw, [])
        
        out_a = get_int_from_bitarray(res['a'], little_endian)
        out_b = get_int_from_bitarray(res['b'], little_endian)
        
        if overflow:
            out_cout = get_int_from_bitarray(res['cout'], little_endian)
            return out_a, out_b, out_cout
            
        return out_a, out_b

    def run_and_verify(self, adder_fn, val_a, val_b, a_len, b_len, overflow=False):
        gate = adder_fn(a_len, b_len, overflow)
        # Integers in this project typically use Big-Endian (little_endian=False)
        little_endian = False
        
        if overflow:
            out_a, out_b, out_cout = self._setup_and_run(val_a, val_b, a_len, b_len, gate, True, little_endian)
            expected_sum = val_a + val_b
            expected_b = expected_sum % (1 << b_len)
            expected_cout = 1 if expected_sum >= (1 << b_len) else 0
            
            assert out_b == expected_b, f"Sum error: {val_a} + {val_b} = {expected_sum}, expected b={expected_b}, got {out_b}"
            assert out_cout == expected_cout, f"Cout error: {val_a} + {val_b} = {expected_sum}, expected cout={expected_cout}, got {out_cout}"
        else:
            out_a, out_b = self._setup_and_run(val_a, val_b, a_len, b_len, gate, False, little_endian)
            expected_b = (val_a + val_b) % (1 << b_len)
            assert out_b == expected_b, f"Sum error: {val_a} + {val_b} (mod 2^{b_len}), expected {expected_b}, got {out_b}"
            
        assert out_a == val_a, f"Input A destroyed: expected {val_a}, got {out_a}"

    @pytest.mark.parametrize("adder_fn", [cuccaro_adder_int, tkk_adder_int])
    @pytest.mark.parametrize("val_a, val_b, a_len, b_len", [
        (3, 2, 3, 3),   # 3+2=5
        (7, 1, 3, 3),   # 7+1=0 (mod 8)
        (0, 5, 3, 3),   # 0+5=5
        (5, 0, 3, 3),   # 5+0=5
        (1, 1, 1, 1),   # 1+1=0 (mod 2)
        (3, 2, 2, 3),   # 3+2=5 (diff lengths)
        (5, 1, 3, 2),   # 5+1=6 -> 2 (mod 4)
    ] + random_cases)
    def test_adders_parametrized(self, adder_fn, val_a, val_b, a_len, b_len):
        self.run_and_verify(adder_fn, val_a, val_b, a_len, b_len, overflow=False)

    @pytest.mark.parametrize("adder_fn", [cuccaro_adder_int, tkk_adder_int])
    @pytest.mark.parametrize("val_a, val_b, a_len, b_len", [
        (7, 1, 3, 3),   # 7+1=8 -> res=0, cout=1
        (3, 3, 2, 2),   # 3+3=6 -> res=2, cout=1
        (1, 0, 1, 1),   # 1+0=1 -> res=1, cout=0
        (15, 1, 4, 4),  # 15+1=16 -> res=0, cout=1
    ])
    def test_adders_overflow_parametrized(self, adder_fn, val_a, val_b, a_len, b_len):
        self.run_and_verify(adder_fn, val_a, val_b, a_len, b_len, overflow=True)

if __name__ == '__main__':
    pytest.main([__file__])
