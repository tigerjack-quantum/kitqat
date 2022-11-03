import itertools
from copy import deepcopy

from bitarray import bitarray
from qat.external.qpus.reversible import RProgram
from qat.external.utils.qroutines import qregs_init as qregs
from qat.external.utils.qroutines.montgomery import arith as marith
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.gates import X, CNOT
from qat.core.console import display
from qat.external.utils.statistics.depth import compute_circuit_depth
from qat.core.util import statistics


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

    depth, max_depth_qubits, dic = compute_circuit_depth(
        circ, include_intermediate=False)
    print(f"depth {depth} on qubits {max_depth_qubits}")

    for op, dep in dic.items():
        print(op, dep)

    sts = statistics(circ)
    print(sts)
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
    # rang[range(prog.qbit_count, prog.qbit_count + k)] = 'anc'
    # ancr = prog.qalloc(k)

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

    qrout = marith.mmul_fixed_n3(n[1:k])
    print(qrout.arity)
    prog1.apply(qrout, ar, br, cr)
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
    # We do not allocate the MSB and LSB, since they're always 1.
    nr = prog.qalloc(len(n) - 2)
    prog.apply(qregs.initialize_qureg_given_bitstring(n[1:k], False), nr)

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

    qrout = marith.mmul3(k)
    prog1.apply(qrout, ar, br, cr, nr)
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

    # INLINE
    # adder = marith.mcadd(k)
    # const_cadder = marith.m_const_cadd(k, n[1:])
    # c_dq = deque([qb for qb in cr])
    # for i, abit in enumerate(reversed(ar)):
    #     print("*" * 15)
    #     print(f"it {i}")
    #     print(f"a[k-i-1] and (c += b)")
    #     prog1.apply(adder, abit, br, c_dq)
    #     _convert_and_print_res(prog1, rang, cr)
    #     print(f"anc[i] = c[k-1]")
    #     prog1.apply(CNOT, c_dq[k-1], ancr[i])
    #     _convert_and_print_res(prog1, rang, cr)
    #     # prog1.apply(adder, ancr[i], nr, c_dq)
    #     print(f"anc[i] and (c = c + {n})")
    #     prog1.apply(const_cadder, ancr[i], c_dq)
    #     _convert_and_print_res(prog1, rang, cr)
    #     print("Shift")
    #     c_dq.rotate()
    #     _convert_and_print_res(prog1, rang, cr)
    #     print("if anc[i] -> X c[0]")
    #     prog1.apply(CNOT, ancr[i], c_dq[0])
    #     _convert_and_print_res(prog1, rang, cr)
    # /INLINE
