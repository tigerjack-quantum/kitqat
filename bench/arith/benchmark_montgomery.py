import random
import time
from test.classical_ref.montgomery import (montgomery_reduce_int,
                                           montgomery_reduce_poly)


def poly_mod(T: int, p: int) -> int:
    #oracle
    t_len = T.bit_length()
    p_len = p.bit_length()
    while t_len >= p_len:
        shift = t_len - p_len
        T ^= (p << shift)
        t_len = T.bit_length()
    return T


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
