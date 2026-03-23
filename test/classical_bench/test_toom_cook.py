import time
import random
import pytest
import  classical_bench.toom_cook as toom

def test_karatsuba_correctness():
    bit_lengths = [8, 16, 64, 256, 1024, 2048]
    
    for bits in bit_lengths:
        x = random.getrandbits(bits)
        y = random.getrandbits(bits)
        
        expected = x * y
        result = toom.karatsuba_int(x, y, threshold=16)
        
        assert result == expected, f"Error with {bits}-bit numbers!"

def test_karatsuba_performance():
    bits = 4096
    x = random.getrandbits(bits)
    y = random.getrandbits(bits)
    
    print(f"\n--- Multiplication Benchmark for {bits} bits ---")
    
    start_base = time.perf_counter()
    expected = x * y
    end_base = time.perf_counter()
    time_base = end_base - start_base
    
    start_kara = time.perf_counter()
    result = toom.karatsuba_int(x, y, threshold=64)
    end_kara = time.perf_counter()
    time_kara = end_kara - start_kara
    
    print(f"Native multiplication (*) time: {time_base:.6f} seconds")
    print(f"Custom Karatsuba time:          {time_kara:.6f} seconds")
    
    assert result == expected