import logging
from typing import TYPE_CHECKING, Dict

from qat.core.variables import Variable

if TYPE_CHECKING:
    from qat.lang.AQASM import Circuit

LOGGER = logging.getLogger(__name__)


def get_variables_from_circuit(circuit: 'Circuit') -> Dict[str, Variable]:
    dic = {}
    for name, value in circuit.var_dic.items():
        dic[name] = get_variable_from_circuit(circuit, name)
    return dic


def get_variable_from_circuit(circuit: 'Circuit', var_name: str) -> Variable:
    value = circuit.var_dic[var_name]
    if value.value.type == 0:
        vtype = int
    elif value.value.type == 1:
        vtype = float
    else:
        raise Exception(f"type {value.value.type} still not convertable")
    var = Variable(var_name, vtype)
    return var
