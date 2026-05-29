import time
import random
import pytest
from test.classical_ref.montgomery import montgomery_reduce_int, montgomery_reduce_poly

#
random.seed(42)

def poly_mod(T: int, p: int) -> int:
    #oracle
    t_len = T.bit_length()
    p_len = p.bit_length()
    while t_len >= p_len:
        shift = t_len - p_len
        T ^= (p << shift)
        t_len = T.bit_length()
    return T

class TestMontgomeryInt:

    @pytest.mark.parametrize(
        "p",
        [
            3, 7, 13, 257, 1048573,      
            random.getrandbits(64) | 1,  
            random.getrandbits(256) | 1,
            random.getrandbits(1024) | 1,
        ]
    )
    def test_montgomery_int_correctness(self, p):
        
        r = p.bit_length()
        R = 1 << r
        
        # Generate a random number less than p
        A = random.randint(0, p - 1)
        
        # Multiply 
        T = A * R  
        
        result = montgomery_reduce_int(T, p)
        assert result == A

    def test_montgomery_int_performance(self):
        
        bits = 2048
        p = random.getrandbits(bits) | 1
        T = random.getrandbits(2 * bits)
        
        print(f"\n--- Montgomery Int F_p Benchmark ({bits} bits) ---")
        
        start_base = time.perf_counter()
        _ = T % p  
        end_base = time.perf_counter()
        time_base = end_base - start_base
        
        start_mont = time.perf_counter()
        _ = montgomery_reduce_int(T, p)
        end_mont = time.perf_counter()
        time_mont = end_mont - start_mont
        
        print(f"Native Python modulo (%) time: {time_base:.6f} seconds")
        print(f"Custom Montgomery REDC time:   {time_mont:.6f} seconds")


class TestMontgomeryPoly:

    @pytest.mark.parametrize(
        "p",
        [
            3, 7, 11, 19, 27,            
            random.getrandbits(64) | 1,  
            random.getrandbits(256) | 1,
            random.getrandbits(512) | 1,
        ]
    )
    def test_montgomery_poly_correctness(self, p):
        
        r = p.bit_length() - 1
        
        A = random.getrandbits(r) if r > 0 else 0
        T_trick = A << r  
        
        res_trick = montgomery_reduce_poly(T_trick, p)
        assert res_trick == A

        T_rand = random.getrandbits(2 * r)
        res_rand = montgomery_reduce_poly(T_rand, p)
        
       
        expected_mod = poly_mod(T_rand, p)
        actual_mod = poly_mod(res_rand << r, p)
        
        assert actual_mod == expected_mod

    def test_montgomery_poly_performance(self):
       
        bits = 1024
        p = random.getrandbits(bits) | 1
        r = p.bit_length() - 1
        T = random.getrandbits(2 * r)
        
        print(f"\n--- Montgomery Poly F_2^m Benchmark ({bits} bits) ---")
        
       
        start_base = time.perf_counter()
        _ = poly_mod(T, p)
        end_base = time.perf_counter()
        time_base = end_base - start_base
        
       
        start_mont = time.perf_counter()
        _ = montgomery_reduce_poly(T, p)
        end_mont = time.perf_counter()
        time_mont = end_mont - start_mont
        
        print(f"Standard Poly Division time: {time_base:.6f} seconds")
        print(f"Montgomery  time: {time_mont:.6f} seconds")

if __name__ == '__main__':
    pytest.main([__file__])