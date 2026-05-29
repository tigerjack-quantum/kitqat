__author__ = "Federico Pinto <federico.pinto@mail.polimi.it>"
# Author: Federico Pinto
import pytest
from qat.lang.AQASM import Program, X
from qat.qpus import PyLinalg

from qatext.qroutines.algebraic.gf2x.adders import qft_adder_int


def simulate_addition(a_val, b_val, a_len, b_len, overflow=False):
    prog = Program()
    q_a = prog.qalloc(a_len)
    q_b = prog.qalloc(b_len)

    if overflow:
        q_ov = prog.qalloc(1)
        target_wires = list(q_ov) + list(q_b)
    else:
        target_wires = list(q_b)

    for i, bit in enumerate(format(a_val, f"0{a_len}b")):
        if bit == "1":
            prog.apply(X, q_a[i])

    for i, bit in enumerate(format(b_val, f"0{b_len}b")):
        if bit == "1":
            prog.apply(X, q_b[i])

    adder = qft_adder_int(a_len, b_len, overflow)
    if overflow:
        prog.apply(adder, q_a, q_b, q_ov)
    else:
        prog.apply(adder, q_a, q_b)

    circuit = prog.to_circ()
    qpu = PyLinalg()
    result = qpu.submit(circuit.to_job())

    best_sample = max(result, key=lambda s: s.probability)

    res_bits = "".join([best_sample.state.bitstring[q.index] for q in target_wires])
    return int(res_bits, 2)


@pytest.mark.parametrize(
    "a, b, n",
    [
        (1, 1, 2),
        (3, 2, 3),
        (7, 7, 4),
        (0, 5, 3),
    ],
)
def test_qft_adder_no_overflow(a, b, n):
    res = simulate_addition(a, b, n, n, False)
    assert res == (a + b) % (2**n)


@pytest.mark.parametrize(
    "a, b, n",
    [
        (1, 1, 1),
        (3, 1, 2),
        (7, 7, 3),
    ],
)
def test_qft_adder_with_overflow(a, b, n):
    res = simulate_addition(a, b, n, n, True)
    assert res == (a + b)


def test_different_lengths():
    """Test addition with inputs of different lengths."""
    res = simulate_addition(2, 1, 2, 3, False)
    assert res == 3


if __name__ == "__main__":
    pytest.main([__file__])
