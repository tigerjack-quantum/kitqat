import logging

import qat.lang.AQASM.classarith
from qat.lang.AQASM.gates import CNOT #, AbstractGate
from qat.lang.AQASM.routines import QRoutine
from qatext.qpus.reversible import inspect_state_reversible_qroutine
from qatext.qroutines.qregs_init import copy_register
from qatext.utils.qatmgmt.routines import QRoutineWrapper
from qat.lang.AQASM.misc import build_gate

# membership_check = AbstractGate("ARRAY_MEMBERSHIP_CHECK", [int],
#                                 arity=lambda n, m: n * m + m + 1)

LOGGER = logging.getLogger(__name__)


@build_gate("ARRAY_MEMBERSHIP_CHECK", [int, int], lambda n, m: n * m + m + 1)
def membership_check(n, m):
    """Given an array of quantum registers of $n$ cells, each one having $m$
    qubits, returns 1 on an output qubit if the array contains a specific value.

    Input:
    - quantum register containing a value
    - quantum array that will be checked for such value
    - output qubit

    """
    routinew = QRoutineWrapper(QRoutine())
    qreg_value = routinew.qregs_array_wires(1, m, "value", int)[0]
    qarray = routinew.qregs_array_wires(n, m, "array", int)
    qbit_out = routinew.qregs_array_wires(1, 1, "out", str)[0][0]
    qarray2 = routinew.qregs_array_wires(n, 1, "array2", str)
    routinew.set_ancillae(qarray2)

    with routinew.compute():
        for q_a, q_a2 in zip(qarray, qarray2):
            (q_a == qreg_value).evaluate(output=q_a2)
    for i in range(n):
        routinew.apply(CNOT, qarray2[i], qbit_out)

    routinew.uncompute()

    return routinew
