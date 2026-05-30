__authors__ = [
    "Federico Pinto <federico.pinto@mail.polimi.it>",
    "Simone Perriello <sperriello@proton.me>",
]

import random
from test.classical_ref.montgomery import (montgomery_reduce_int,
                                           montgomery_reduce_poly)

import pytest

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

if __name__ == '__main__':
    pytest.main([__file__])
