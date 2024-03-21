from qatext.synthesis.roots.paulis import nrootx
from qat.lang.AQASM import CCNOT, CNOT, AbstractGate, H, QRoutine, S, T, X
from qat.lang.AQASM.misc import build_gate

MCMTX = AbstractGate("MCMTX", [int, int, int], arity=lambda x, y, _: x + y)
MTCCNOT = AbstractGate("MTCCNOT", [int, bool], arity=lambda x, _: x + 2)


@build_gate("X", [], arity=lambda: 1)
def x():
    """Transform an X gate into HSSH.

    It can be used in stabilizer circuits.
    """
    qfun = QRoutine()
    wires = qfun.new_wires(1)
    qfun.apply(H, wires[0])
    qfun.apply(S, wires[0])
    qfun.apply(S, wires[0])
    qfun.apply(H, wires[0])
    return qfun


@build_gate("CCNOT", [], arity=lambda: 3)
def ccnot():
    """CCNOT implemented with CNOT, H and T gates."""
    qfun = QRoutine()
    wires = qfun.new_wires(3)
    qfun.set_ancillae(anc)
    qfun.apply(H, wires[2])
    qfun.apply(CNOT, wires[1], wires[2])
    qfun.apply(T.dag(), wires[2])
    qfun.apply(CNOT, wires[0], wires[2])
    qfun.apply(T, wires[2])

    qfun.apply(CNOT, wires[1], wires[2])
    qfun.apply(T.dag(), wires[2])
    qfun.apply(CNOT, wires[0], wires[2])
    qfun.apply(T, wires[1])
    qfun.apply(T, wires[2])

    qfun.apply(CNOT, wires[0], wires[1])
    qfun.apply(H, wires[2])

    qfun.apply(T, wires[0])
    qfun.apply(T.dag(), wires[1])
    qfun.apply(CNOT, wires[0], wires[1])
    return qfun


@build_gate("MTCCNOT", [int, bool])
def mccnot_sqrroot(n_tgts, global_phase_enabled):
    # nielsen chuang, p.182
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


@build_gate("MTCCNOT", [int, bool])
def mccnot_ht(n_tgts, global_phase_enabled):
    """With this gate, we always have a global phase.

    That is, the result is equivalent to a multi-target toffoli up to a
    global phase.
    """
    # nielsen chuang, p.182
    qfun = QRoutine()
    ctrls = qfun.new_wires(2)
    tgts = qfun.new_wires(n_tgts)

    for qb in tgts:
        qfun.apply(H, qb)
        qfun.apply(CNOT, ctrls[1], qb)
    for qb in tgts:
        qfun.apply(T.dag(), qb)
        qfun.apply(CNOT, ctrls[0], qb)
    for qb in tgts:
        qfun.apply(T, qb)
        qfun.apply(CNOT, ctrls[1], qb)
    for qb in tgts:
        qfun.apply(T.dag(), qb)
        qfun.apply(CNOT, ctrls[0], qb)
    qfun.apply(T.dag(), ctrls[1])
    qfun.apply(CNOT, ctrls[0], ctrls[1])
    qfun.apply(T.dag(), ctrls[1])
    qfun.apply(CNOT, ctrls[0], ctrls[1])
    qfun.apply(T, ctrls[0])
    qfun.apply(S, ctrls[1])
    for qb in tgts:
        qfun.apply(T, qb)
    for qb in tgts:
        qfun.apply(H, qb)
    return qfun


@build_gate("MTCCCNOT", [int, bool])
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
def mcmtx_vshape(n_ctrls: int, n_tgts: int, max_unsplitted_ctrls=2) -> QRoutine:
    qfun = QRoutine()
    ctrls = qfun.new_wires(n_ctrls)
    tgts = qfun.new_wires(n_tgts)
    _common(qfun, ctrls, tgts, max_unsplitted_ctrls)

    if max_unsplitted_ctrls < 2:
        raise ValueError(
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
        qfun.apply(CCNOT, ctrls[cidx], ancs[aidx], ancs[aidx + 1])

    for tqb in tgts:
        qfun.apply(CCNOT, ctrls[-1], ancs[-1], tqb)

    for cidx, aidx in zip(
        reversed(range(2, len(ctrls) - 1)), reversed(range(len(ancs) - 1))
    ):
        qfun.apply(CCNOT, ctrls[cidx], ancs[aidx], ancs[aidx + 1])
    qfun.apply(CCNOT, ctrls[0], ctrls[1], ancs[0])


# @build_gate("MCMTX", [int, int, str, int])
# def mcmtx_barenco1(n_ctrls: int,
#                   n_tgts: int,
#                   max_unsplitted_ctrls=2) -> QRoutine:
#     qfun = QRoutine()
#     ctrls = qfun.new_wires(n_ctrls)
#     tgts = qfun.new_wires(n_tgts)
#     _common(qfun, ctrls, tgts, max_unsplitted_ctrls)
#     _barenco1(qfun, ctrls, tgts, max_unsplitted_ctrls)
#     return qfun

# def _barenco1(qfun, ctrls, tgts, max_unsplitted_ctrls):
#     # https://arxiv.org/abs/quant-ph/9503016
#     if len(ctrls) < 0:
#         pass
#     elif len(ctrls) == 0:
#         # qc.x(qrs[0])
#         for qb in tgts:
#             qfun.apply(X, qb)
#     elif len(ctrls) == 1:
#         # qc.cx(qrs[0], qrs[1])
#         for qb in tgts:
#             qfun.apply(CNOT, qb)
#     elif len(ctrls) == 2 and max_unsplitted_ctrls > 2:
#             for qb in tgts:
#                 qfun.apply(CCNOT, ctrls, qb)
#     else:
#         # allqbs = [qb for qb in itertools.chain(ctrls, tgts, ancs)]
#         if len(ctrls) > 3:
#             anc = qfun.new_wires(1)
#             qfun.set_ancillae(anc)
#         else:
#             anc = None
#         _barenco1_support(qfun, ctrls, tgts, anc)
#         # _barenco1_support(qfun, allqbs)

# def _barenco1_support(qfun, ctrls, tgts, anc):
# # def _barenco1_support(qfun, allqbs):
#     if len(ctrls) == 2:
#         qfun.apply(mccnot(len(tgts)), ctrls, tgts)
#     elif len(ctrls) == 3:
#         input(tgts)
#         bah = (~mcccnot)(len(tgts))
#         qfun.apply(mcccnot(len(tgts)), ctrls, tgts)
#     else:
#         # qfun = QRoutine()
#         # ctrls = qfun.new_wires(4)
#         # tgts = qfun.new_wires(n_tgts)
#         qfun2 = nrootx(2)

#         for qb in tgts:
#             qfun.apply(qfun2.ctrl(), ctrls[3], qb)
#         _barenco1_support(qfun, ctrls[:-1], [ctrls[-1]], None)
#         # qfun.apply(mcccnot(1, pi / 4), ctrls[:-1], [ctrls[-1]])
#         for qb in tgts:
#             qfun.apply(qfun2.dag().ctrl(), ctrls[3], qb)
#         _barenco1_support(qfun, ctrls[:-1], [ctrls[-1]], None)
#         # qfun.apply(mcccnot(1, pi / 4), ctrls[:-1], [ctrls[-1]])
#         _barenco1_support(qfun, ctrls[:-1], anc, None)
#         # qfun.apply(mcccnot(n_tgts, pi / 8), ctrls[:-1], tgts)
#         for qb in tgts:
#             qfun.apply(CNOT, anc[0], qb)
#         # This is huge
#         _barenco1_support(qfun, ctrls[:-1], anc, None)

# # def _barenco1_support(qfun, ctrls, tgts, anc):
# # # def _barenco1_support(qfun, allqbs):
# #     if len(ctrls) == 3:
# #         qfun.apply(mcccnot(len(tgts), pi / 4), ctrls, tgts)
# #     elif len(ctrls) == 4:
# #         qfun.apply(mccccnot(len(tgts)), ctrls, tgts)
# #     else:  # qrs[0], qrs[n-2] is the controls, qrs[n-1] is the target, and qancilla as working qubit
# #         n = len(ctrls) + 2
# #         m1 = ceil(n / 2)
# #         # allqbs = [qb for qb in itertools.chain(ctrls, tgts, anc)]
# #         _barenco1_support(qfun, ctrls[:m1], tgts, ctrls[m1])
# #         _barenco1_support(qfun, ctrls[m1:], tgts, anc)
# #         _barenco1_support(qfun, [*ancs[m1:n - 1], qancilla, ancs[n - 1]],
# #                           ancs[m1 - 1])
# #         _barenco1_support(qfun, [*ancs[:m1], qancilla], ancs[m1])
# #         _barenco1_support(qfun, [*ancs[m1:n - 1], qancilla, ancs[n - 1]],
# #                           ancs[m1 - 1])

# def _barenco0():
#     # https://arxiv.org/abs/quant-ph/9503016
#     pass

# @build_gate("MCCCCNOT", [int, int])
# def mccccnot(n_tgts):
#     qfun = QRoutine()
#     ctrls = qfun.new_wires(4)
#     tgts = qfun.new_wires(n_tgts)
#     qfun2 = (~nrootx)(-pi / 2)

#     for qb in tgts:
#         qfun.apply(qfun2.ctrl(), ctrls[3], qb)
#     qfun.apply(mcccnot(1, pi / 4), ctrls[:-1], [ctrls[-1]])
#     for qb in tgts:
#         qfun.apply(qfun2.dag().ctrl(), ctrls[3], qb)
#     qfun.apply(mcccnot(1, pi / 4), ctrls[:-1], [ctrls[-1]])
#     qfun.apply(mcccnot(n_tgts, pi / 8), ctrls[:-1], tgts)
