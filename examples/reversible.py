from qat.lang.AQASM.gates import CCNOT, CNOT, SWAP, X
from qat.lang.AQASM.program import Program
from qat.pylinalg import PyLinalg
from qatext.qpus.reversible import RProgram, inspect_rprogram_state
from qatext.qroutines.qregs_init import initialize_qureg_given_int
from qatext.utils.qatmgmt.program import ProgramWrapper


def ex1():
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
    rpr = RProgram.circuit_to_rprogram(cr)
    print(rpr.rbits)


def ex2(n):
    n_qubits = (n - 1).bit_length()
    pr = Program()
    # ProgramWrapper adds a few functionalities to Program
    prw = ProgramWrapper(pr)
    # allocate n quantum registers on pr, each one composed of n_qubits
    qarray_ints = prw.qregs_array_alloc(
        n,
        n_qubits,
        "MyQuantumArray",
        int,
    )
    for i in range(n):
        qroutine_init = initialize_qureg_given_int(i,
                                                   n_qubits,
                                                   little_endian=False)
        pr.apply(qroutine_init, qarray_ints[i])

    state_str = inspect_rprogram_state(prw, [])
    print(state_str)


def main():
    # ex1()
    ex2(4)


if __name__ == '__main__':
    main()
