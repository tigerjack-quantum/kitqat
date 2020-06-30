# from numpy import ceil, pi
from qat.external.utils.qroutines.roots.paulis import nrootx
from qat.lang.AQASM import CCNOT, CNOT, QRoutine, X, AbstractGate
from qat.lang.AQASM.misc import build_gate

MCMTX = AbstractGate("MCMTX", [int, int, int], arity=lambda x, y, _: x + y)


@build_gate("MCCNOT", [int, bool])
def mccnot(n_tgts, global_phase_enabled):
    qfun = QRoutine()
    ctrls = qfun.new_wires(2)
    tgts = qfun.new_wires(n_tgts)

    qfun2 = nrootx(2, global_phase_enabled)
    for qb in tgts:
        qfun.apply(qfun2.ctrl(), ctrls[1], qb)
    qfun.apply(CNOT, ctrls[0], ctrls[1])
    for qb in tgts:
        qfun.apply(qfun2.dag().ctrl(), ctrls[1], qb)
    qfun.apply(CNOT, ctrls[0], ctrls[1])
    for qb in tgts:
        qfun.apply(qfun2.dag().ctrl(), ctrls[0], qb)
    return qfun


@build_gate("MCCCNOT", [int, bool])
def mcccnot(n_tgts, global_phase_enabled):
    # https://arxiv.org/abs/quant-ph/9503016 pag. 17

    qfun = QRoutine()
    ctrls = qfun.new_wires(3)
    tgts = qfun.new_wires(n_tgts)
    qfun2 = nrootx(4, global_phase_enabled)

    for qb in tgts:
        qfun.apply(qfun2.ctrl(), ctrls[0], qb)
    qfun.apply(CNOT, ctrls[0], ctrls[1])
    for qb in tgts:
        qfun.apply(qfun2.dag().ctrl(), ctrls[1], qb)
    qfun.apply(CNOT, ctrls[0], ctrls[1])
    for qb in tgts:
        qfun.apply(qfun2.ctrl(), ctrls[1], qb)
    qfun.apply(CNOT, ctrls[1], ctrls[2])
    for qb in tgts:
        qfun.apply(qfun2.dag().ctrl(), ctrls[2], qb)
    qfun.apply(CNOT, ctrls[0], ctrls[2])
    for qb in tgts:
        qfun.apply(qfun2.ctrl(), ctrls[2], qb)
    qfun.apply(CNOT, ctrls[1], ctrls[2])
    for qb in tgts:
        qfun.apply(qfun2.dag().ctrl(), ctrls[2], qb)
    qfun.apply(CNOT, ctrls[0], ctrls[2])
    for qb in tgts:
        qfun.apply(qfun2.ctrl(), ctrls[2], qb)
    return qfun


def _common(qfun, ctrls, tgts, max_unsplitted_ctrls):
    n_ctrls = len(ctrls)

    if n_ctrls <= max_unsplitted_ctrls:
        for qb in tgts:
            qfun.apply(X.ctrl(n_ctrls), ctrls, qb)
        return qfun


# def mcmtx(n_ctrls: int,
@build_gate("MCMTX", [int, int, int])
def mcmtx_vshape(n_ctrls: int,
                 n_tgts: int,
                 max_unsplitted_ctrls=2) -> QRoutine:
    qfun = QRoutine()
    ctrls = qfun.new_wires(n_ctrls)
    tgts = qfun.new_wires(n_tgts)
    _common(qfun, ctrls, tgts, max_unsplitted_ctrls)

    if max_unsplitted_ctrls < 2:
        raise Exception(
            "vshape mode requires CCNOTs, so max_unsplitted_ctrls should be >= 2"
        )
    _vshape_chain(qfun, ctrls, tgts)
    return qfun


def _vshape_chain(qfun, ctrls, tgts):
    if len(ctrls) == 2:
        for qb in tgts:
            qfun.apply(CCNOT, ctrls, qb)
        return

    ancs = qfun.new_wires(len(ctrls) - 2)
    qfun.set_ancillae(ancs)
    qfun.apply(CCNOT, ctrls[0], ctrls[1], ancs[0])

    for cidx, aidx in zip(range(2, len(ctrls) - 1), range(len(ancs) - 1)):
        print(cidx, aidx)
        qfun.apply(CCNOT, ctrls[cidx], ancs[aidx], ancs[aidx + 1])

    for tqb in tgts:
        qfun.apply(CCNOT, ctrls[-1], ancs[-1], tqb)

    # for cqb, aqb in zip(reversed(ctrls[2:-1]), reversed(ancs[1:])):
    # qfun.apply(CCNOT, cqb, aqb)
    for cidx, aidx in zip(reversed(range(2,
                                         len(ctrls) - 1)),
                          reversed(range(len(ancs) - 1))):
        print(cidx, aidx)
        qfun.apply(CCNOT, ctrls[cidx], ancs[aidx], ancs[aidx + 1])
    qfun.apply(CCNOT, ctrls[0], ctrls[1], ancs[0])
