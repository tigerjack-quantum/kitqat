import itertools
from test.common_circuit import CircuitTestCase

from parameterized import parameterized
from qat.external.utils.bits import conversion, misc
from qat.external.utils.qroutines import adder
from qat.external.utils.qroutines import qregs_init as qregs
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.gates import X, SWAP
import sys
from qat.core.console import display
from qat.qpus import PyLinalg
from qat.lang.AQASM import build_gate

# @build_gate("COMP", arity=3)
# def comparator() -> QRoutine:
#     qfun = QRoutine()
#     qfun.apply()


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
    for ab, bb, in itertools.product((False, True), (False, True)):
        print(int(ab), int(bb))
        comparator_exp(ab, bb, False, False)


if __name__ == '__main__':
    main()
