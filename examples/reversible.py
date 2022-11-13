from qat.external.qpus.reversible import RGate, RProgram
from qat.lang.AQASM.gates import CCNOT, CNOT, SWAP, H, X
from qat.lang.AQASM.program import Program
from qat.pylinalg import PyLinalg

def main():
    pr = Program()
    qr = pr.qalloc(5)
    pr.apply(X, qr[0])
    pr.apply(X, qr[4])
    pr.apply(SWAP, qr[4], qr[3])
    pr.apply(CNOT, qr[:2])
    pr.apply(CCNOT, qr[:3])
    pr.apply(SWAP, qr[2], qr[4])
    # # Note that this last 2 gates are not applied since their ctrls are not all 1's
    pr.apply(CCNOT, qr[2:5])
    pr.apply(SWAP.ctrl(3), qr)
    qpu = PyLinalg()
    cr = pr.to_circ()
    res = qpu.submit(cr.to_job())
    sample = None
    for sample in res:
        pass
    assert sample is not None
    breakpoint()
    rpr = RProgram.circuit_to_rprogram(cr)
    print(rpr.rbits)

if __name__ == '__main__':
    main()
