import numpy as np
from qat.lang.AQASM import RX, RY, RZ, AbstractGate, QRoutine


def _peek_rgate(gate):
    if gate == 'X':
        return RX
    elif gate == 'Y':
        return RY
    elif gate == 'Z':
        return RZ
    else:
        raise ValueError(f"Gate {gate} not valid")


def _get_nroot(gate_name, n, global_phase_enabled):
    qfun = QRoutine(1)
    gate = _peek_rgate(gate_name)
    if not global_phase_enabled:
        qfun.apply(gate(np.pi / n), 0)
    else:
        ag = AbstractGate(
            f"MR{gate_name}{np.pi/n}", [], 1,
            lambda: np.exp(np.pi * 1j /
                           (2 * n)) * gate.matrix_generator(np.pi / n))
        qfun.apply(ag(), 0)
    return qfun


def nrootx(n: int, global_phase_enabled=False) -> QRoutine:
    qfun = _get_nroot('X', n, global_phase_enabled)
    return qfun.box(f"{n}rtX")


def nrooty(n: int, global_phase_enabled=False) -> QRoutine:
    qfun = _get_nroot('Y', n, global_phase_enabled)
    return qfun.box(f"{n}rtY")


def nrootz(n: int, global_phase_enabled=False) -> QRoutine:
    qfun = _get_nroot('Z', n, global_phase_enabled)
    return qfun.box(f"{n}rtZ")
