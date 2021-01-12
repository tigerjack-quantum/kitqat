import logging
from typing import TYPE_CHECKING, Dict, Sequence, Tuple

from qat.core.variables import Variable, revert_type

if TYPE_CHECKING:
    from qat.lang.AQASM import Circuit

LOGGER = logging.getLogger(__name__)


def generate_variables_from_circuit(circuit: 'Circuit') -> Dict[str, Variable]:
    dic = {}
    for name, value in circuit.var_dic.items():
        dic[name] = generate_variable_from_circuit(circuit, name)
    return dic


def generate_variable_from_circuit(circuit: 'Circuit',
                                   var_name: str) -> Variable:
    value = circuit.var_dic[var_name]
    vtype = revert_type(value.value.type)
    var = Variable(var_name, vtype)
    return var


def generate_new_var_params_from_circuit(
        circuit: 'Circuit') -> Sequence[Tuple[type, str]]:
    lst = []
    for vname, var in circuit.var_dic:
        vtype = revert_type(var.value.type)
        lst.append((vtype, vname))
    return lst
