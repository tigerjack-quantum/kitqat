import logging
import operator
from functools import reduce

from qat.lang.AQASM.gates import CNOT
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine
from qatext.utils.qatmgmt.routines import QRoutineWrapper

# membership_check = AbstractGate("ARRAY_MEMBERSHIP_CHECK", [int],
#                                 arity=lambda n, m: n * m + m + 1)

LOGGER = logging.getLogger(__name__)


@build_gate("ARRAY_MEMBERSHIP_CHECK", [int, int, bool],
            lambda n, m, _: n * m + m + 1)
def membership_check(n, m, repeated_values_possible=False):
    """Given an array of quantum registers of $n$ cells, each one having $m$
    qubits, returns 1 on an output qubit if the array contains a specific value.

    Input:
    - quantum register containing a value
    - quantum array that will be checked for such value
    - output qubit

    """
    routinew = QRoutineWrapper(QRoutine())
    qreg_value_to_check = routinew.qarray_wires(1, m, "value2chk", int)[0]
    qarray = routinew.qarray_wires(n, m, "array", int)
    qbit_out = routinew.qarray_wires(1, 1, "out", str)[0][0]
    # it will contain the 0/1 bit of the comparisons
    qarray_cmp = routinew.qarray_wires(1, n, "array_cmp", bool)[0]
    routinew.set_ancillae(qarray_cmp)

    with routinew.compute():
        for qreg_val, qbit_cmp in zip(qarray, qarray_cmp):
            (qreg_val == qreg_value_to_check).evaluate(output=qbit_cmp)
    if not repeated_values_possible:
        for i in range(n):
            routinew.apply(CNOT, qarray_cmp[i], qbit_out)
    else:
        or_formula = reduce(operator.or_, qarray_cmp)
        or_formula.evaluate(output=qbit_out)

    routinew.uncompute()

    return routinew
