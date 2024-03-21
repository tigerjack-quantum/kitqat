from qat.lang.AQASM.gates import CCNOT, CNOT, H, X, Y, Z, S
from qat.lang.AQASM.program import Program
from qat.pylinalg import PyLinalg
from qatext.synthesis import cliffordt as ct

qpu = PyLinalg()


def ex1():
    pr = Program()
    qr = pr.qalloc(2)
    X(qr[0])
    Y(qr[0])
    Z(qr[0])
    CNOT(qr)

    cr = pr.to_circ()
    for op in cr.iterate_simple():
        print(op)

    # We initialize a Linker with an empty gate set since we want
    # to override the default Pauli gates implementation
    linker = ct.get_new_cliffordt_linker()
    linker.add_signature(ct.x)
    linker.add_signature(ct.y)
    linker.add_signature(ct.z)
    linker.link(cr)

    for op in cr.iterate_simple():
        print(op)

    cr.display(max_depth=2)


def ex2():
    pr = Program()
    qr = pr.qalloc(3)
    CCNOT(qr)
    linker = ct.get_new_cliffordt_linker()
    linker.add_signature(ct.ccnot1)

    cr = pr.to_circ()
    linker.link(cr)
    cr.display(max_depth=2)

    print(cr.statistics())
    print(cr.depth(default=0, gate_times={"T": 1.0, "D-T": 1.0}))

def ex3():
    pr = Program()
    qr = pr.qalloc(3)
    X(qr[0])
    X(qr[1])

    H(qr[0])
    H(qr[1])
    ct.QAND()(qr)
    linker = ct.get_new_cliffordt_linker()
    linker.add_signature(ct.qand1)
    linker.add_signature(ct.x)

    cr = pr.to_circ()
    linker.link(cr)
    # cr.display(max_depth=2)

    res = qpu.submit(cr.to_job())
    for sample in res:
        if sample.state.bitstring[:2] == '11':
            assert sample.state.bitstring[2] == '1'
        else:
            assert sample.state.bitstring[2] == '0', f"{sample.state.bitstring}"
        print(sample.state.bitstring, sample.amplitude)
        # assert sample.amplitude  == .5, f"{sample}"
    print(cr.depth(default=0, gate_times={"T": 1.0, "D-T": 1.0}))

    
def ex4():
    linker = ct.get_new_cliffordt_linker()
    linker.add_signature(ct.x)
    linker.add_signature(ct.qand1)

    pr = Program()
    qr = pr.qalloc(3)
    H(qr[0])
    H(qr[1])
    ct.QAND()(qr)
    # ct.QAND_DAG()(qr)

    cadd = pr.calloc(1)

    # QAND_DAG implementation original
    # H(qr[2])
    # pr.measure(qr[2], cadd)
    # pr.cc_apply(cadd, X, qr[2])
    # pr.cc_apply(cadd, S, qr[1])
    # pr.cc_apply(cadd, S, qr[0])
    # pr.cc_apply(cadd, CNOT, qr[0:2])
    # pr.cc_apply(cadd, S.dag(), qr[1])
    # pr.cc_apply(cadd, CNOT, qr[0:2])
    
    # QAND_DAG implementation adaptation, since a measured qubit is not
    # reusable

    # Note that the additional qubit qadd is not always necessary, since we
    # could reuse the ancillary qubit of the QAND gate.
    qadd = pr.qalloc(1)
    H(qr[2])
    CNOT(qr[2], qadd)
    #
    pr.measure(qadd, cadd)
    pr.cc_apply(cadd, X, qr[2])
    pr.cc_apply(cadd, S, qr[1])
    pr.cc_apply(cadd, S, qr[0])
    pr.cc_apply(cadd, CNOT, qr[0:2])
    pr.cc_apply(cadd, S.dag(), qr[1])
    pr.cc_apply(cadd, CNOT, qr[0:2])
    # pr.cc_apply(cadd, X, qadd)
    

    # linker.add_signature(ct.qand_dag2)

    cr = pr.to_circ()
    # for op in cr.iterate_simple():
    #     print(op)

    print("*" * 80)

    linker.link(cr)
    # linker.link(cr)
    # cr.display(max_depth=2)

    # for op in cr.iterate_simple():
    #     print(op)

    res = qpu.submit(cr.to_job())
    for sample in res:
        # if sample.state.bitstring[:2] == '11':
        #     assert sample.state.bitstring[2] == '1'
        # else:
        #     assert sample.state.bitstring[2] == '0', f"{sample.state.bitstring}"
        print(sample.state.bitstring, sample.amplitude)

    # res = qpu.submit(cr.to_job(qubits=[qadd]))
    # for sample in res:
    #     print(sample.state.bitstring, sample.amplitude)


def main():
    ex4()


if __name__ == "__main__":
    main()
