from typing import TYPE_CHECKING, Dict, List

from qat.lang.AQASM import X, Y, Z

if TYPE_CHECKING:
    from qat.lang.AQASM import (Term, Gate)


def produce_term_gates(term: 'Term') -> Dict[int, List['Gate']]:
    r"""Given a term (the term used by an observable), produce a map of gates to be
    applied on each qbits in order to produce a circuit equivalent to the "OBS"
    mode of the QLM. Basically, the idea is to apply :math: <0|C^{\dag} \hat{O}
    C|0>, where the :math: \hat{0} part is one term of an observable. For now
    it only works with Pauli operators.

    """
    qbits_to_gates: Dict[int, 'Gate'] = {}
    for op, qbit in zip(term.op, term.qbits):
        if op == "X":
            qbits_to_gates[qbit] = [X]
        elif op == "Y":
            qbits_to_gates[qbit] = [Y]
        elif op == "Z":
            qbits_to_gates[qbit] = [Z]
        else:
            raise ValueError("The term just works with Pauli operators")
    return qbits_to_gates
