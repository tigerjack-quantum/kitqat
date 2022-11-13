"""Enumerate all the bitstrings of length k and weight p."""

import logging

import numpy as np
# from qat.lang.AQASM.gates import CNOT, RY, X
# from qat.lang.AQASM.routines import QRoutine
# from qat.lang.AQASM.misc import build_gate

logger = logging.getLogger(__name__)

def _find_set_bits(x, n):
    """Auxiliary function for lee_brickell."""
    bits = []
    for i in range(n):
        mask = 1 << i # 2**i
        if mask & x:
            bits.append(i)
    return bits

def col_add(k, col_res, col_addend, controls):
    """Column addition for the lee_brickell method controlled by a quantum
    register.

    Args:
        col_res (int): column where the result of the addition is stored.
        col_addend (int): column to add to col_res.
        controls (list): quantum register that controls the operation.
    """
    for i in range(k):
        controls.append((i, col_addend))
        print(f"X.ctrl({controls}, Hq[{i}, {col_res}]")
        controls.pop()
    print("*"*20)

# @build_gate("CWENC", [int, int, int])
def igate(k: int, p: int, r: int):
    # c = QRoutine()
    # wires = qf.new_wires(k)
    # wires = [0] * k
    # anc = qf.new_wires(2)
    # n-2 -> 0, n-1 -> 1 
    setb = (1 << p) - 1 # 2**p - 1
    limit = (1 << r) # 2**r

    while setb < limit:
        columns_to_add = _find_set_bits(setb, r)
        for i in columns_to_add:
            col_add(k, k+r, i + k, [])
            # c.add(k, col_add(k+r, i + k, []))

        # # CHECK WEIGHTS
        # # put the weight of the syndrome
        # c.add(self.syndrome_weight().on_qubits(*range(c.nqubits)))
        # # add the negated version of t - p to put qubits to 1
        # c.add(self.add_negates_for_check(self.ancillas[::-1], weight - p))
        # c.add(self.add_one(self.counter[::-1], [*self.ancillas]))
        # c.add(self.add_negates_for_check(self.ancillas[::-1], weight - p))
        # c.add(self.syndrome_weight().invert().on_qubits(*range(c.nqubits)))
        # # / CHECK WEIGHT

        # # Reverse columns to add
        for i in columns_to_add:
            col_add(k, k+r, i + k, [])
            c.add(self.col_add(self.n, i + self.k, []))

        C = setb & -setb
        R = setb + C
        setb = int(((R ^ setb) >> 2) / C) | int(R)

    # print(c.summary())
    # return c

def main():
    k = 12
    r = 3
    p = 2
    print(f"k: {k}, r: {r}, p: {p}")
    igate (k,p,r)


if __name__ == '__main__':
    main()
