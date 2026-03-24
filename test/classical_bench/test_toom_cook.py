import time
import random
import pytest
import  classical_bench.toom_cook as toom


random.seed(42)

class TestToomCookInt:

    @pytest.mark.parametrize(
        "val_a, val_b",
        [
            (0, 0),          
            (1, 0),          
            (1, 1),        
            (15, 15),        
            (16, 16),       
            (25, 23),       
            (1023, 1024),    
            (random.getrandbits(16), random.getrandbits(8)),
            (random.getrandbits(64), random.getrandbits(64)),     # 64-bit
            (random.getrandbits(256), random.getrandbits(256)),   # 256-bit
            (random.getrandbits(1024), random.getrandbits(1024)), # 1024-bit
            (random.getrandbits(2048), random.getrandbits(2048)), # 2048-bit
        ]
    )
    def test_karatsuba_int_correctness(self, val_a, val_b):
        
        expected = val_a * val_b
        result = toom.karatsuba_int(val_a, val_b, threshold=16)
        
      
        assert result == expected


    def test_karatsuba_performance(self):
        bits = 2048
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

class TestToomCookPoly:

    @pytest.mark.parametrize(
        "val_a, val_b",
        [
            # base case
            (0, 0),  # 0 * 0 = 0
            (1, 1),  # 1 * 1 = 1
            
            # edge cases 
            (0, 3),  # Null element: 0 * (x+1) = 0
            (1, 3),  # Identity: 1 * (x+1) = x+1 
            (2, 2),  # Base polynomial: x * x = x^2 
            (3, 3),  # Cross terms cancellation: (x+1) * (x+1) = x^2 + 1 
            (7, 3),  # (x^2+x+1) * (x+1) = x^3 + 1 
            (5, 5),  # (x^2+1) * (x^2+1) = x^4 + 1 
            (6, 7),  # (x^2+x) * (x^2+x+1) = x^4 + x 
            
            
            (15, 15), 
            (16, 16), 
            
            # Asymmetric
            (random.getrandbits(32), random.getrandbits(8)),
            
            # Large random polynomials
            (random.getrandbits(64), random.getrandbits(64)),
            (random.getrandbits(256), random.getrandbits(256)),
            (random.getrandbits(512), random.getrandbits(512)),
            (random.getrandbits(1024), random.getrandbits(1024)),
        ]
    )
    def test_karatsuba_poly_correctness(self, val_a, val_b):
        
        expected = toom.clmul(val_a, val_b)

        result = toom.karatsuba_poly(val_a, val_b, threshold=16)
        
      
        assert result == expected, f"Polynomial error: {val_a} * {val_b} should be {expected}, but got {result}"

    def test_karatsuba_poly_performance(self):
        
        bits = 1024 
        x = random.getrandbits(bits)
        y = random.getrandbits(bits)
        
        print(f"\n--- Polynomial Multiplication Benchmark for {bits} bits ---")
        
        start_base = time.perf_counter()
        expected =  toom.clmul(x, y)
        end_base = time.perf_counter()
        time_base = end_base - start_base
        
    
        start_kara = time.perf_counter()
        result = toom.karatsuba_poly(x, y, threshold=64)
        end_kara = time.perf_counter()
        time_kara = end_kara - start_kara
        
        print(f"Standard clmul time: {time_base:.6f} seconds")
        print(f"Karatsuba F_2^m time:         {time_kara:.6f} seconds")
        
        assert result == expected

class TestToom3Int:

    @pytest.mark.parametrize(
        "val_a, val_b",
        [
            (0, 0),          # Zero
            (1, 0),          # Zero by one
            (1, 1),          # Identity
            (15, 15),        # Below threshold (threshold = 16)
            (16, 16),        # Exactly on threshold
            
            # Asymmetric
            (1023, 1024),    
            (random.getrandbits(16), random.getrandbits(8)),
            
            #Large random numbers
            (random.getrandbits(64), random.getrandbits(64)),     # 64-bit
            (random.getrandbits(256), random.getrandbits(256)),   # 256-bit
            (random.getrandbits(1024), random.getrandbits(1024)), # 1024-bit
            (random.getrandbits(2048), random.getrandbits(2048)), # 2048-bit
        ]
    )
    def test_toom3_int_correctness(self, val_a, val_b):
        
        expected = val_a * val_b
        
        result = toom.toom3_int(val_a, val_b, threshold=16)
    
        assert result == expected, f"Error: {val_a} * {val_b} should be {expected}, but got {result}"

    def test_toom3_int_performance(self):

        bits = 2048
        x = random.getrandbits(bits)
        y = random.getrandbits(bits)
        
        print(f"\n--- Toom-Cook 3 Integer Benchmark for {bits} bits ---")
        
        
        start_base = time.perf_counter()
        expected = x * y
        end_base = time.perf_counter()
        time_base = end_base - start_base
        
        
        start_toom = time.perf_counter()
        result = toom.toom3_int(x, y, threshold=64)
        end_toom = time.perf_counter()
        time_toom = end_toom - start_toom
        
        print(f"Native multiplication (*) time: {time_base:.6f} seconds")
        print(f"Custom Toom-Cook 3 time:        {time_toom:.6f} seconds")
        
        assert result == expected

class TestToom3Poly:

    @pytest.mark.parametrize(
        "val_a, val_b",
        [
            (0, 0), (1, 1),
            (0, 3), (1, 3), (2, 2), (3, 3), (7, 3), (5, 5), (6, 7),
            (15, 15), (16, 16),
            # Asymmetric
            (random.getrandbits(32), random.getrandbits(8)),
            # Large random polynomials
            (random.getrandbits(64), random.getrandbits(64)),
            (random.getrandbits(256), random.getrandbits(256)),
            (random.getrandbits(1024), random.getrandbits(1024)),
        ]
    )
    def test_toom3_poly_correctness(self, val_a, val_b):
        
        expected = toom.clmul(val_a, val_b)
        result = toom.toom3_poly(val_a, val_b, threshold=16)
        
        assert result == expected

    def test_toom3_poly_performance(self):
        
        bits = 16384 
        x = random.getrandbits(bits)
        y = random.getrandbits(bits)
        
        print(f"\n--- The Ultimate F_2^m Polynomial Benchmark ({bits} bits) ---")
        
        # clmul
        start_base = time.perf_counter()
        expected = toom.clmul(x, y)
        end_base = time.perf_counter()
        time_base = end_base - start_base
        
        # Karatsuba
        start_kara = time.perf_counter()
        result_kara = toom.karatsuba_poly(x, y, threshold=2048)
        end_kara = time.perf_counter()
        time_kara = end_kara - start_kara

        # Toom-Cook 3 
        start_toom = time.perf_counter()
        result_toom = toom.toom3_poly(x, y, threshold=2048)
        end_toom = time.perf_counter()
        time_toom = end_toom - start_toom
        
        
        print(f"Standard clmul (O(n^2)) time:   {time_base:.6f} seconds")
        print(f"Karatsuba (O(n^1.58)) time:     {time_kara:.6f} seconds")
        print(f"Toom-Cook 3 (O(n^1.46)) time:   {time_toom:.6f} seconds")
        
       
        assert result_kara == expected 
        assert result_toom == expected
if __name__ == '__main__':
    pytest.main([__file__])