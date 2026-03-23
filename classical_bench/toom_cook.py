
def karatsuba_int(x: int, y: int, threshold: int = 16) -> int:
    # Karatsuba multiplication 
    # Base case for recursion 
    if x < threshold or y < threshold:
        return x * y

    # Calculate the bit length
    n = max(x.bit_length(), y.bit_length())
    m = n // 2

    # Split x and y into high and low parts
    mask = (1 << m) - 1
    
    x_low = x & mask
    x_high = x >> m
    
    y_low = y & mask
    y_high = y >> m

    # 3 recursive multiplications 
    z0 = karatsuba_int(x_low, y_low, threshold)
    z2 = karatsuba_int(x_high, y_high, threshold)
    z1 = karatsuba_int(x_low + x_high, y_low + y_high, threshold)

    # Recombine: Z2 * 2^(2m) + (Z1 - Z2 - Z0) * 2^m + Z0
    return (z2 << (2 * m)) + ((z1 - z2 - z0) << m) + z0


