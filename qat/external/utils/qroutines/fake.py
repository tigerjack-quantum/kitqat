from qat.lang.AQASM import QRoutine, Program, Qbit

from typing import Dict, List


# @build_gate("", [str])
def fake(name):
    qf = QRoutine(1)
    return qf.box(name)


def add_fake_following_pattern(program: Program,
                               pattern: Dict[str, List[Qbit]]):
    for k, qbits in pattern.items():
        for i, qbit in enumerate(qbits):
            program.apply(fake(f"{k}_{i}"), qbit)
