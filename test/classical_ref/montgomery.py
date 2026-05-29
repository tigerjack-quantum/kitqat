from test.classical_ref.toom_cook import clmul

def egcd(a: int, b: int) -> tuple[int, int, int]:
    
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
        
    return old_r, old_s, old_t

def montgomery_reduce_int(T: int, p: int) -> int:
   
    r = p.bit_length()
    R = 1 << r
    
    # p_prime = -p^(-1) mod R
    g, inv_x, _ = egcd(p, R)
    if g != 1:
        raise Exception("Modular inverse does not exist")
    p_prime = (-inv_x) % R

    
    mask = (1 << r) - 1
    
    # m = ((T mod R) * p') mod R
    m = ((T & mask) * p_prime) & mask
    
    # t = (T + m * p) / R
    t = (T + m * p) >> r
    
    
    if t >= p:
        return t - p
    return t


def montgomery_reduce_poly(T: int, p: int) -> int:
    
    if (p & 1) == 0:
        raise ValueError("Polynomial must have a constant term of 1 to be invertible")
        
    r = p.bit_length() - 1  # Degree of the polynomial
    
    # polynomial inverse  p' = -p^(-1) mod R
    p_prime = 1
    for i in range(1, r):
        prod = clmul(p_prime, p)
        if (prod >> i) & 1:
            p_prime ^= (1 << i)


    mask = (1 << r) - 1
    
    # m = ((T mod R) * p') mod R
    m = clmul(T & mask, p_prime) & mask
    
    # t = (T ^ (m * p)) / R
    t = (T ^ clmul(m, p)) >> r
    
    if t.bit_length() >= p.bit_length():
        t ^= p
        
    return t
