from qat.lang.AQASM.gates import CNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.qint import QInt
from qat.lang.AQASM.routines import QRoutine


@build_gate('FANOUT', [int, int], lambda n, m: n * m + m)
def fanout(n, m):
    qf = QRoutine()
    qr_val = qf.new_wires(m, QInt)
    qrs_a = []
    for _ in range(n):
        qrs_a.append(qf.new_wires(m, QInt))

    # fan out
    for i in range(n):
        qf.apply(copy(m), qr_val, qrs_a[i])
        # for qb1, qb2 in zip(qr_val, qrs_a[i]):
        #     qf.apply(CNOT, qb1, qb2)
    return qf

@build_gate('COPY', [int], lambda n: 2*n)
def copy(n):
    qf = QRoutine()
    qr_val = qf.new_wires(n)
    qr_val2 = qf.new_wires(n)
    for qb1, qb2 in zip(qr_val, qr_val2):
        qf.apply(CNOT, qb1, qb2)
    return qf
