
def karatsuba_int(x: int, y: int, threshold: int = 16) -> int:
    
    # Base case 
    if x < threshold or y < threshold:
        return x * y

    # bit length
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


def clmul(x: int, y: int) -> int:
   
    result = 0
    while y > 0:
        if y & 1:         
            result ^= x    
        x <<= 1            
        y >>= 1            
    return result

def karatsuba_poly(x: int, y: int, threshold: int = 16) -> int:
   
    # Base case
    if x < threshold or y < threshold:
        return clmul(x, y)

    n = max(x.bit_length(), y.bit_length())
    m = n // 2

    # Split x and y 
    mask = (1 << m) - 1
    
    x_low = x & mask
    x_high = x >> m
    
    y_low = y & mask
    y_high = y >> m

    # 3 recursive multiplications
    z0 = karatsuba_poly(x_low, y_low, threshold)
    z2 = karatsuba_poly(x_high, y_high, threshold)
    z1 = karatsuba_poly(x_low ^ x_high, y_low ^ y_high, threshold)

    # Recombine: Z2 * x^(2m) XOR (Z1 XOR Z2 XOR Z0) * x^m XOR Z0
    cross_term = z1 ^ z2 ^ z0
    return (z2 << (2 * m)) ^ (cross_term << m) ^ z0

def toom3_int(x: int, y: int, threshold: int = 16) -> int:
    
    # Base case
    if x < threshold or y < threshold:
        return x * y

    
    n = max(x.bit_length(), y.bit_length())
    m = (n + 2) // 3

    mask = (1 << m) - 1

    
    # Split 
    x0 = x & mask
    x1 = (x >> m) & mask
    x2 = x >> (2 * m)
    y0 = y & mask
    y1 = (y >> m) & mask
    y2 = y >> (2 * m)

    # evaluation 
    px_0 = x0
    px_1 = x2 + x1 + x0
    px_m1 = x2 - x1 + x0
    px_2 = (x2 << 2) + (x1 << 1) + x0  
    px_inf = x2

    py_0 = y0
    py_1 = y2 + y1 + y0
    py_m1 = y2 - y1 + y0
    py_2 = (y2 << 2) + (y1 << 1) + y0
    py_inf = y2

    # recursive multiplications at the evaluation points
    w0 = toom3_int(px_0, py_0, threshold)
    w1 = toom3_int(px_1, py_1, threshold)
    wm1 = toom3_int(px_m1, py_m1, threshold)
    w2 = toom3_int(px_2, py_2, threshold)
    winf = toom3_int(px_inf, py_inf, threshold)

   # interpolation
    z0 = w0
    z4 = winf
    
    # Intermediate variables 
    A = (w1 - wm1) // 2
    B = (w1 + wm1) // 2
    C = (w2 - w0) // 2
    
    #coefficients
    z2 = B - z0 - z4
    z3 = (C - A - (z2 << 1) - (z4 << 3)) // 3
    z1 = A - z3

    result = (z4 << (4 * m)) + (z3 << (3 * m)) + (z2 << (2 * m)) + (z1 << m) + z0
    return result


def toom3_div(p: int) -> int:
   
    q = 0
    q_prev = 0
    # Process the polynomial bit by bit
    for i in range(p.bit_length()):
        p_i = (p >> i) & 1
        q_i = p_i ^ q_prev
        q |= (q_i << i)
        q_prev = q_i
    return q


def toom3_poly(x: int, y: int, threshold: int = 16) -> int:
    
    # Base case
    if x < threshold or y < threshold:
        return clmul(x, y)

    n = max(x.bit_length(), y.bit_length())
    m = (n + 2) // 3

    mask = (1 << m) - 1

    # split
    x0 = x & mask
    x1 = (x >> m) & mask
    x2 = x >> (2 * m)

    y0 = y & mask
    y1 = (y >> m) & mask
    y2 = y >> (2 * m)

    # evaluation
    px_0 = x0
    px_inf = x2
    px_1 = x0 ^ x1 ^ x2
    px_x = x0 ^ (x1 << 1) ^ (x2 << 2)
    px_x1 = px_0 ^ px_1 ^ px_x

    py_0 = y0
    py_inf = y2
    py_1 = y0 ^ y1 ^ y2
    py_x = y0 ^ (y1 << 1) ^ (y2 << 2)
    py_x1 = py_0 ^ py_1 ^ py_x

    # mul
    w0 = toom3_poly(px_0, py_0, threshold)
    winf = toom3_poly(px_inf, py_inf, threshold)
    w1 = toom3_poly(px_1, py_1, threshold)
    wx = toom3_poly(px_x, py_x, threshold)
    wx1 = toom3_poly(px_x1, py_x1, threshold)

    # interpolation
    z0 = w0
    z4 = winf

    S = w0 ^ w1 ^ wx ^ wx1
    z3 = toom3_div(S >> 1)
    K = w0 ^ w1 ^ winf ^ z3
    R = wx ^ w0 ^ (winf << 4) ^ (z3 << 3) ^ (K << 1)
    z2 = toom3_div(R >> 1)
    z1 = K ^ z2

    
    result = (z4 << (4 * m)) ^ (z3 << (3 * m)) ^ (z2 << (2 * m)) ^ (z1 << m) ^ z0
    
    return result    
    
    return result