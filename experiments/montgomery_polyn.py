from qat.external.utils.qroutines import qregs_init as qregs
from qat.external.utils.qroutines.montgomery import arith as marith
from qat.lang.AQASM.program import Program

from qat.lang.AQASM.gates import CCNOT, CNOT
from qat.core.console import display
from qat.external.qpus.reversible import RProgram
from qat.core.console import display

from collections import deque
from bitarray import bitarray
from copy import deepcopy
import itertools
from qat.pylinalg import PyLinalg

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

def _convert_and_print_res(pr: Program, rang: range, dq: list):
        circ = pr.to_circ(include_matrices=False, submatrices_only=True)
        rcr = RProgram.circuit_to_rprogram(circ, rang)
        res_whole = rcr.rbits
        res_whole_named = rcr.get_result_by_name()
        print(res_whole_named)
        print(f"res w/ deque {[res_whole[i.index] for i in dq]}")
        print([qb.index for qb in dq])


def main():
    k = 4  # GF(2^k)
    n = '10011'  # x^4 + x + 1
    r = '10000'  # x^4
    rmod = '0011'  # x + 1
    rinv = '1110'
    # ninv = '0001'
    # npr = '1111'
    little_endian = False

    # r mod n
    prog = Program()
    rang = {range(prog.qbit_count, prog.qbit_count + len(n)): 'n'}
    nr = prog.qalloc(len(n))
    rang[range(prog.qbit_count, prog.qbit_count + len(rmod) + 1)] = 'r'
    rinvr = prog.qalloc(len(rinv) + 1)

    prog.apply(qregs.initialize_qureg_given_bitstring(n, little_endian), nr)
    prog.apply(qregs.initialize_qureg_given_bitstring('0' + rinv, little_endian), rinvr)

    print("*" * 20)
    print("Assuming a and b are polynomials in montgomery form")
    print("Performing ADD, i.e.a + b")
    a = '1101'
    b = '1001'
    rang[range(prog.qbit_count, prog.qbit_count + k + 1)] = 'a'
    ar = prog.qalloc(k + 1)
    rang[range(prog.qbit_count, prog.qbit_count + k + 1)] = 'b'
    br = prog.qalloc(k + 1)
    rang[range(prog.qbit_count, prog.qbit_count + k + 1)] = 'c'
    cr = prog.qalloc(k + 1)
    rang[range(prog.qbit_count, prog.qbit_count + k + 1)] = 'anc'
    ancr = prog.qalloc(k + 1)
    # print(rang)

    prog.apply(qregs.initialize_qureg_given_bitstring('0' + a, False), ar)
    prog.apply(qregs.initialize_qureg_given_bitstring('0' + b, False), br)

    # Working
    # res_exp = bitarray('0100')
    # print(f"res_exp {poly_str(res_exp)} {res_exp}")
    # prog1 = deepcopy(prog)
    # prog1.apply(marith.madd(k + 1), ar, br)
    # circ = prog1.to_circ(include_matrices=False, submatrices_only=True)
    # rcr = RProgram.circuit_to_rprogram(circ, rang)
    # res = rcr.filter_result_by_name('b')['b']
    # print(f"res     {poly_str(res)} {res}")
    # assert are_polynomials_eq(res_exp, res)

    print("Performing MULT, i.e.a * b * r^{-1}")
    res_exp = bitarray('0101')
    print(f"Exp {poly_str(res_exp)}; {res_exp}")
    # should be a * b * r^{-1}
    prog1 = deepcopy(prog)
    # print(len(ar))
    # print(len(br))
    # print(len(cr))
    # print(len(nr))

    # #
    # dq = deque([qb for qb in cr])
    # # c idxs are [2k + 1, ..., 3k]
    # adder = marith.mcadd(k + 1)
    # for i, abit in enumerate(reversed(ar[1:])):
    #     print("-" * 20)
    #     print(f"it {i}")
    #     # test
    #     _convert_and_print_res(prog1, rang, dq)
    #     # end test
    #     print("c = a[i] and (c xor b")
    #     prog1.apply(adder, abit, br, dq)
    #     _convert_and_print_res(prog1, rang, dq)
    #     print("c = c[k] and (c xor n ")
    #     prog1.apply(CNOT, dq[k], ancr[i])
    #     prog1.apply(adder, ancr[i], nr, dq)
    #     _convert_and_print_res(prog1, rang, dq)
    #     print("Shifting")
    #     dq.rotate()
    #     _convert_and_print_res(prog1, rang, dq)

    qrout = marith.mmul(k)
    prog1.apply(qrout, ar, br, cr, nr, ancr)

    circ = prog1.to_circ(include_matrices=False, submatrices_only=True)
    print(circ.nbqbits)
    # qpu = PyLinalg()
    # res = qpu.submit(circ.to_job())
    # print(res)
    # for sample in res:
    #     print(sample)
    # display(circ, max_depth=2)
    rcr = RProgram.circuit_to_rprogram(circ, rang)
    dq_fake = [qb for qb in cr[1:]] + [cr[0]]
    _convert_and_print_res(prog1, rang, dq_fake)

    # res_whole = rcr.rbits
    # print(f"res w/ deque {[res_whole[i.index] for i in cr]}")
    # res = rcr.filter_result_by_name('c')['c']
    # print(f"res     {poly_str(res)} {res}")
    # print(f"res w/ deque {[res_whole[i.index] for i in dq]}")
    # assert are_polynomials_eq(res_exp, res), f"exp {res_exp}, obt {res}"

    # print(rpr.qbits)
    # print(rpr.rregs)


if __name__ == '__main__':
    main()
