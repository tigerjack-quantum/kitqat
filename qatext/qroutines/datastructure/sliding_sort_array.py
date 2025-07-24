from qat.lang.AQASM.gates import CNOT, SWAP, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.qint import QInt
from qat.lang.AQASM.routines import QRoutine


@build_gate('SLIDING_SORT_INSERT', [int, int], lambda n, m: n * m + m)
def insert(n, m):
    """n cells, each one of size m.
    Expect qregs in this order: X, A
    """
    qf = QRoutine()
    qr_val = qf.new_wires(m, QInt)
    qrs_a = []
    for _ in range(n):
        qrs_a.append(qf.new_wires(m, QInt))
    qrs_ai = []
    for _ in range(n):
        _qr = qf.new_wires(m, QInt)
        qrs_ai.append(_qr)
        qf.set_ancillae(_qr)
    qr_aii = qf.new_wires(n, QInt)
    qf.set_ancillae(qr_aii)
    # return qf # OK

    # fan out
    for i in range(n):
        for qb1, qb2 in zip(qr_val, qrs_ai[i]):
            qf.apply(CNOT, qb1, qb2)

    # ... also to the last cell of A
    for qb1, qb2 in zip(qr_val, qrs_a[n - 1]):
        qf.apply(CNOT, qb1, qb2)
    # return qf # OK

    # compare
    for qr_a, qr_ai, qb_aii in zip(qrs_a, qrs_ai, qr_aii):
        (qr_ai <= qr_a).evaluate(output=qb_aii)
        # qf.apply(add(m+1, m).dag(), qr_a, qb_aii, qr_ai)
    # return qf # OK

    # swap 1
    for i in range(n - 1):
        qr_a, qr_ai, qb_aii = qrs_a[i], qrs_ai[i + 1], qr_aii[i]
        for qb_a, qb_ai in zip(qr_a, qr_ai):
            qf.apply(SWAP.ctrl(), qb_aii, qb_ai, qb_a)
    # return qf

    # swap 2
    for i in range(n - 1):
        qr_a, qr_ai, qb_aii = qrs_a[i + 1], qrs_ai[i + 1], qr_aii[i]
        for qb_a, qb_ai in zip(qr_a, qr_ai):
            qf.apply(SWAP.ctrl(), qb_aii, qb_a, qb_ai)
    # return qf

    # compare
    for qr_a, qr_ai, qb_aii in zip(qrs_a, qrs_ai, qr_aii):
        (qr_ai <= qr_a).evaluate(output=qb_aii)

    # fan out
    for i in range(n):
        for qb1, qb2 in zip(qr_val, qrs_ai[i]):
            qf.apply(X.ctrl(), qb1, qb2)

    return qf


@build_gate('SLIDING_SORT_DELETE', [int, int], lambda n, m: n * m + m)
def delete(n, m):
    qf = QRoutine()
    qw = qf.new_wires(n * m + m)
    qf1 = insert(n, m).dag()
    qf.apply(qf1, *qw)
    return qf
