import itertools

from qat.lang.AQASM.program import Program
from qat.lang.AQASM.gates import X, SWAP
from qat.pylinalg import PyLinalg
from qat.external.qroutines.arith.cuccaro_arith import subtractor, adder
from qat.external.qroutines import qregs_init

qpu = PyLinalg()

def sub_test():
    n = 3
    pr = Program()
    qr1 = pr.qalloc(n)
    const = pr.qalloc(n)

    pr.apply(qregs_init.initialize_qureg_given_int(7, n, False), qr1)
    pr.apply(qregs_init.initialize_qureg_given_int(5, n, False), const)
    

    # ALT. 1
    # pr.apply(subtractor(n, n, False, False), const, qr1)
    # for qb in qr1:
    #     pr.apply(X, qb)
    # pr.apply(qregs_init.initialize_qureg_given_int(4, n, False), const)
    # pr.apply(qregs_init.initialize_qureg_given_int(1, n, False), const)
    # pr.apply(adder(n, n, False, False), const, qr1)

    # ALT. 2
    pr.apply(subtractor(n, n, False, False), qr1, const)
    for qb1, qb2 in zip(qr1, const):
        pr.apply(SWAP, qb1, qb2)
    for qb in const:
        pr.apply(X, qb)
    pr.apply(adder(n, n, False, False), qr1, const)
    for qb in const:
        pr.apply(X, qb)
    # pr.apply(subtractor(n, n, False, False), qr1, const)
    

    
    # for qb1, qb2 in zip(qr1, const):
    #     pr.apply(SWAP, qb1, qb2)

    cr = pr.to_circ()
    res = qpu.submit(cr.to_job())
    for sample in res:
        print(sample.state.bitstring)



def comparator_exp(ab: bool, bb: bool, h1b: bool, h2b: bool):
    """Test that a is smaller than b and, if that is the case, store 1 in
    cout."""
    # Prepare qubits
    # bits = misc.get_required_bits(a_int, b_int)
    pr = Program()

    a = pr.qalloc(1)
    b = pr.qalloc(1)
    cout = pr.qalloc(1)

    if ab:
        pr.apply(X, a)
    if bb:
        pr.apply(X, b)


    # </ WORRKS!!!
    # adder before
    # pr.apply(X, a)
    # pr.apply(X.ctrl(2), a, b, cout)
    # pr.apply(X, a)
    # # adder cout + b -> cout + a
    # pr.apply(X.ctrl(), cout, b)
    # pr.apply(X, b)
    # pr.apply(X.ctrl(2), cout, b, a)
    # pr.apply(X, b)
    #/>
    # </ ccnot a,b,c; cswap c, a,b
    pr.apply(X, a)
    pr.apply(X.ctrl(2), a, b, cout)
    pr.apply(X, a)
    # 
    # pr.apply(SWAP.ctrl(), cout, a, b)
    pr.apply(X.ctrl(),  a, b)
    pr.apply(X.ctrl(2), cout, b, a)
    pr.apply(X.ctrl(), a, b)
    #/>


    # h1 = pr.qalloc(1)
    # h2 = pr.qalloc(1)
    # if h1b:
    #     pr.apply(X, h1)
    # if h2b:
    #     pr.apply(X, h2)
    ## # adder cout + hb -> hb
    # pr.apply(CNOT, cout, h2)
    # pr.apply(X, h2)
    # pr.apply(X.ctrl(2), cout, h2, h1)
    # pr.apply(X, h2)


    cr = pr.to_circ()
    # display(cr, max_depth=1)
    # expected = 1 if (not ab and bb) else 0

    qpu = PyLinalg()
    res = qpu.submit(cr.to_job())
    for sample in res:
        print(sample.state)
        # if sample.state.lsb_int == expected:
        #     print(sample.state)
        #     break

def main():
    # for ab, bb, h1b, h2b in itertools.product((False, True), (False, True), (False, True), (False, True)):
    #     # print(int(ab), int(bb))
    #     print(int(h1b), int(h2b))
    #     comparator_exp(ab, bb, h1b, h2b)
    sub_test()
    # for ab, bb, in itertools.product((False, True), (False, True)):
    #     print(int(ab), int(bb))
    #     comparator_exp(ab, bb, False, False)


if __name__ == '__main__':
    main()
