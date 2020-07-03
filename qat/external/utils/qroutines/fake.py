from typing import Dict, List

from qat.lang.AQASM import AbstractGate, Program, Qbit, QRoutine


def fake_gate(name: str, arity: int) -> AbstractGate:
    """Just a fake qroutine used to add some visualization effect. """
    qf = QRoutine(arity)
    return qf.box(name)
