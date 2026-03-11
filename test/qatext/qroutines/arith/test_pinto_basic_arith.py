from test.common_pytest import (REVERSIBLE_ON, REVERSIBLE_ON_REASON,
                                CircuitTestHelpers)

import numpy as np
import pytest
import qat.lang.AQASM.classarith
# from parameterized import parameterized
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import get_states_from_program_wrapper
from qatext.qroutines.qregs_mgmt import qregs_init as qi
from qatext.qroutines.datastructure.sliding_sort_array import (delete, insert,
                                                               insert_lw)
from qatext.utils.bits.conversion import (get_int_from_bitarray,
                                          get_ints_from_bitarray)
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qroutines.algebraic.gf2x.Pinto_basic_arith import adder2bit, sub2bit, mul2bit, adder_n_bit


class TestPintoBasicArith:


    @pytest.mark.parametrize(
        "val_a, val_b",
        [
            (0, 0),  # 0 XOR 0 = 0
            (0, 1),  # 0 XOR 1 = 1
            (1, 0),  # 1 XOR 0 = 1
            (1, 1),  # 1 XOR 1 = 0
        ]
    )
    def test_adder2bit(self, val_a, val_b):
        
        prw = ProgramWrapper(Program())


        qr_a = prw.qarray_alloc(1, 1, "a", int)
        qr_b = prw.qarray_alloc(1, 1, "b", int)

    
        init_a = qi.initialize_qureg_given_int(val_a, 1, False)
        init_b = qi.initialize_qureg_given_int(val_b, 1, False)
        
        prw.apply(init_a, qr_a[0])
        prw.apply(init_b, qr_b[0])

        
        gate_add = adder2bit()
        prw.apply(gate_add, qr_a[0], qr_b[0])

  
        res = get_states_from_program_wrapper(prw, [])

     
        out_a = get_int_from_bitarray(res['a'], False)
        out_b = get_int_from_bitarray(res['b'], False)

       
        expected_b = val_a ^ val_b
        
        assert out_a == val_a
        assert out_b == expected_b, f"Errore calcolo: {val_a} + {val_b} in GF(2) fa {expected_b}, non {out_b}"

    def test_sub2bit_alias(self):
        """Un piccolo test rapido per verificare che l'alias sub2bit funzioni esattamente come adder2bit"""
        prw = ProgramWrapper(Program())
        qr_a = prw.qarray_alloc(1, 1, "a", int)
        qr_b = prw.qarray_alloc(1, 1, "b", int)

       
        prw.apply(qi.initialize_qureg_given_int(1, 1, False), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(1, 1, False), qr_b[0])

      
        gate_sub = sub2bit()
        prw.apply(gate_sub, qr_a[0], qr_b[0])

        res = get_states_from_program_wrapper(prw, [])
        out_b = get_int_from_bitarray(res['b'], False)

       
        assert out_b == 0, f"Il sottrattore ha fallito, 1-1 dovrebbe dare 0, non {out_b}"


    @pytest.mark.parametrize(
        "val_a, val_b",
        [
            (0, 0),  # 0 * 0 = 0
            (0, 1),  # 0 * 1 = 0
            (1, 0),  # 1 * 0 = 0
            (1, 1),  # 1 * 1 = 1
        ]
    )
    
    def test_mul2bit(self, val_a, val_b):
    
        prw = ProgramWrapper(Program())

        
        qr_a = prw.qarray_alloc(1, 1, "a", int)
        qr_b = prw.qarray_alloc(1, 1, "b", int)
        qr_out = prw.qarray_alloc(1, 1, "out", int) 
       
        prw.apply(qi.initialize_qureg_given_int(val_a, 1, False), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, 1, False), qr_b[0])

        
        gate_mul = mul2bit()
        prw.apply(gate_mul, qr_a[0], qr_b[0], qr_out[0])

        
        res = get_states_from_program_wrapper(prw, [])

        
        out_a = get_int_from_bitarray(res['a'], False)
        out_b = get_int_from_bitarray(res['b'], False)
        final_out = get_int_from_bitarray(res['out'], False)

        
        expected_out = val_a & val_b
        
        
        assert out_a == val_a
        assert out_b == val_b
        assert final_out == expected_out, f"Errore: {val_a} * {val_b} fa {expected_out}, non {final_out}"

    @pytest.mark.parametrize(
        "val_a, val_b, nbits",
        [
            # --- Casi da 1 bit ---
            (1, 1, 1),  # Auto-annullamento: 1 + 1 = 0
            
            # --- Casi da 2 bit ---
            (0, 3, 2),  # Zero + Max (11) = 3
            (2, 3, 2),  # Misto: 10 + 11 = 01 (1)
            (3, 3, 2),  # Auto-annullamento Max: 11 + 11 = 0
            
            # --- Casi da 3 bit ---
            (0, 7, 3),  # Zero + Max (111) = 7
            (5, 3, 3),  # Misto: 101 (5) + 011 (3) = 110 (6)
            (7, 7, 3),  # Auto-annullamento Max: 111 + 111 = 0
            (2, 5, 3),  # Misto: 010 (2) + 101 (5) = 111 (7)
        ]
    )
    def test_adder_n_bit(self, val_a, val_b, nbits):
        """Testa l'addizionatore N-bit per polinomi con casi limite fino a 3 bit."""
        prw = ProgramWrapper(Program())

        # Allochiamo registri grandi "nbits"
        qr_a = prw.qarray_alloc(1, nbits, "a", int)
        qr_b = prw.qarray_alloc(1, nbits, "b", int)

        # Inizializziamo i qubit con i valori scelti
        prw.apply(qi.initialize_qureg_given_int(val_a, nbits, False), qr_a[0])
        prw.apply(qi.initialize_qureg_given_int(val_b, nbits, False), qr_b[0])

        # Applichiamo il nostro gate N-bit!
        gate_add_n = adder_n_bit(nbits)
        prw.apply(gate_add_n, qr_a[0], qr_b[0])

        # Simuliamo istantaneamente
        res = get_states_from_program_wrapper(prw, [])

        # Estraiamo i risultati e li convertiamo in interi
        out_a = get_int_from_bitarray(res['a'], False)
        out_b = get_int_from_bitarray(res['b'], False)

        # Calcoliamo il risultato matematico atteso (XOR classico)
        expected_b = val_a ^ val_b
        
        # Verifichiamo
        assert out_a == val_a
        assert out_b == expected_b, f"Errore con {nbits} bit: {val_a} + {val_b} doveva dare {expected_b}, ma ha dato {out_b}"
if __name__ == '__main__':
    pytest.main([__file__])