import itertools
from copy import deepcopy

from bitarray import bitarray
from qat.external.qpus.reversible import RProgram
from qat.external.utils.qroutines import qregs_init as qregs
from qat.external.utils.qroutines.montgomery import arith as marith
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.gates import X, CNOT
from qat.core.console import display


def poly_str(a: bitarray):
    ls = []
    for i, bit in enumerate(a):
        if bit:
            power = len(a) - i - 1
            if power == 0:
                ls.append('1')
            elif power == 1:
                ls.append('x')
            else:
                ls.append(f'x^{power}')
    return ' + '.join(ls)


def are_polynomials_eq(*a: bitarray):
    g1 = itertools.groupby(map(lambda x: degree(x), a))
    g2 = itertools.groupby(map(lambda x: x.count(1), a))
    return next(g1, True) and not next(g1, False) and next(
        g2, True) and not next(g2, False)


def degree(a: bitarray) -> int:
    if not a.any():
        return -1
    degree = len(a) - a.find(1) - 1
    return degree


def _convert_and_print_res(pr: Program, rang: dict, dq: list):
    circ = pr.to_circ(include_matrices=False, submatrices_only=True)
    # display(circ, max_depth=4)
    rcr = RProgram.circuit_to_rprogram(circ, rang)
    res_whole = rcr.rbits
    res_whole_named = rcr.get_result_by_name()
    print(res_whole_named)
    print(f"deque {[qb.index for qb in dq]}")
    print(f"res w/ deque {[res_whole[i.index] for i in dq]}")
    print(f"N of qubits {len(rcr.rbits)}")
    return rcr


def _fix_modulus(k, n, a, b):
    prog = Program()
    rang = {}
    print("*" * 50)
    print("FIX MODULUS")
    print("Assuming a and b are polynomials in montgomery form")
    print("Performing ADD, i.e. a + b")
    rang[range(prog.qbit_count, prog.qbit_count + k)] = 'a'
    ar = prog.qalloc(k)
    rang[range(prog.qbit_count, prog.qbit_count + k)] = 'b'
    br = prog.qalloc(k)
    rang[range(prog.qbit_count, prog.qbit_count + k)] = 'c'
    cr = prog.qalloc(k)
    rang[range(prog.qbit_count, prog.qbit_count + k)] = 'anc'
    ancr = prog.qalloc(k)

    prog.apply(qregs.initialize_qureg_given_bitstring(a, False), ar)
    prog.apply(qregs.initialize_qureg_given_bitstring(b, False), br)

    # Working
    res_exp = bitarray('0100')
    print(f"res_exp {poly_str(res_exp)} {res_exp}")
    prog1 = deepcopy(prog)
    prog1.apply(marith.madd(k), ar, br)
    circ = prog1.to_circ(include_matrices=False, submatrices_only=True)
    rcr = RProgram.circuit_to_rprogram(circ, rang)
    res = rcr.filter_result_by_name('b')['b']
    print(f"res     {poly_str(res)} {res}")
    assert are_polynomials_eq(res_exp, res), f"{res_exp} vs {res}"

    print("Performing MULT, i.e.a * b * r^{-1}")
    res_exp = bitarray('0101')
    print(f"Exp {poly_str(res_exp)}; {res_exp}")
    # should be a * b * r^{-1}
    prog1 = deepcopy(prog)

    qrout = marith.mmul_fixed_n2(k, n[1:])
    prog1.apply(qrout, ar, br, cr, ancr)
    circ = prog1.to_circ(include_matrices=False, submatrices_only=True)
    print(circ.nbqbits)
    rcr = _convert_and_print_res(prog1, rang, cr)
    res = rcr.filter_result_by_name('c')['c']
    assert are_polynomials_eq(res_exp, res), f"{res_exp} vs {res}"


def _var_modulus(k, n, a, b):
    prog = Program()
    rang = {}
    print("*" * 50)
    print("VAR MODULUS")
    print("Assuming a and b are polynomials in montgomery form")
    a = '1101'
    rang[range(prog.qbit_count, prog.qbit_count + k)] = 'a'
    ar = prog.qalloc(k)
    prog.apply(qregs.initialize_qureg_given_bitstring(a, False), ar)

    b = '1001'
    rang[range(prog.qbit_count, prog.qbit_count + k)] = 'b'
    br = prog.qalloc(k)

    rang[range(prog.qbit_count, prog.qbit_count + k)] = 'c'
    cr = prog.qalloc(k)

    rang[range(prog.qbit_count, prog.qbit_count + k)] = 'anc'
    ancr = prog.qalloc(k)

    rang[range(prog.qbit_count, prog.qbit_count + len(n))] = 'n'
    # We do not allocate the MSB, since it's always 1. Should be the same for
    # the last, but we'll check later
    nr = prog.qalloc(len(n) - 1)
    prog.apply(qregs.initialize_qureg_given_bitstring(n[1:], False), nr)

    prog.apply(qregs.initialize_qureg_given_bitstring(b, False), br)

    print("Performing ADD, i.e. a + b")
    res_exp = bitarray('0100')
    print(f"res_exp {poly_str(res_exp)} {res_exp}")
    prog1 = deepcopy(prog)
    prog1.apply(marith.madd(k), ar, br)
    circ = prog1.to_circ(include_matrices=False, submatrices_only=True)
    rcr = RProgram.circuit_to_rprogram(circ, rang)
    res = rcr.filter_result_by_name('b')['b']
    print(f"res     {poly_str(res)} {res}")
    assert are_polynomials_eq(res_exp, res)

    print("Performing MULT, i.e.a * b * r^{-1}")
    res_exp = bitarray('0101')
    print(f"Exp {poly_str(res_exp)}; {res_exp}")
    # should be a * b * r^{-1}

    prog1 = deepcopy(prog)

    qrout = marith.mmul2(k)
    prog1.apply(qrout, ar, br, cr, nr, ancr)
    rcr = _convert_and_print_res(prog1, rang, cr)
    res = rcr.filter_result_by_name('c')['c']
    assert are_polynomials_eq(res_exp, res), f"{res_exp} vs {res}"
    print(f"N of qubits {len(rcr.rbits)}")


def main():
    k = 4  # GF(2^k)
    n = '10011'  # x^4 + x + 1
    r = '10000'  # x^4
    rmod = '0011'  # x + 1
    rinv = '1110'
    # ninv = '0001'
    # npr = '1111'
    a = '1101'
    b = '1001'

    # little_endian = False
    _fix_modulus(k, n, a, b)
    _var_modulus(k, n, a, b)


if __name__ == '__main__':
    main()
