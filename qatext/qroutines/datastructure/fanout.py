from qat.lang.AQASM.gates import CNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine


@build_gate('FANOUT', [int, int], lambda n, m: n * m + m)
def fanout(n, m):
    qf = QRoutine()
    qr_val = qf.new_wires(m)
    qrs_a = []
    for _ in range(n):
        qrs_a.append(qf.new_wires(m))

    # registers that already contain the value
    available = [qr_val]

    targets = list(qrs_a)

    while targets:
        new_available = []
        for src in available:
            if not targets:
                break

            tgt = targets.pop(0)

            # copy src -> tgt
            qf.apply(copy(m), src, tgt)

            new_available.append(tgt)

        # newly created copies can broadcast next round
        available += new_available

    return qf

@build_gate('COPY', [int], lambda n: 2*n)
def copy(n):
    qf = QRoutine()
    qr_val = qf.new_wires(n)
    qr_val2 = qf.new_wires(n)
    for qb1, qb2 in zip(qr_val, qr_val2):
        qf.apply(CNOT, qb1, qb2)
    return qf
