import itertools
import logging
from typing import TYPE_CHECKING, Dict, Optional, Sequence, Tuple, Union

import numpy as np
from qat.core.circuit_builder.matrix_util import (get_param_generator,
                                                  get_predef_generator)
from qat.external.utils.numpy.qstate_manipulation import (
    get_conjugate_from_matrix, get_ctrl_from_matrix, get_dagger_from_matrix,
    get_transpose_from_matrix)
from qat.external.utils.qatmgmt import variables
from qat.lang.AQASM import (CCNOT, CNOT, CSIGN, ISWAP, PH, RX, RY, RZ,
                            SQRTSWAP, SWAP, AbstractGate, H, I, ParamGate, S,
                            T, X, Y, Z)

if TYPE_CHECKING:
    from qat.lang.AQASM import (Circuit, Gate, Variable)
    from qat.comm.datamodel.ttypes import Op

LOGGER = logging.getLogger(__name__)

# TODO change to get_param_generator or get_predef_generator
GATE_SET_QAT = {
    'H': [H, H.extract_signatures()[0].matrix_generator()],
    'X': [X, X.extract_signatures()[0].matrix_generator()],
    'Y': [Y, Y.extract_signatures()[0].matrix_generator()],
    'Z': [Z, Z.extract_signatures()[0].matrix_generator()],
    'I': [I, I.extract_signatures()[0].matrix_generator()],
    'S': [S, S.extract_signatures()[0].matrix_generator()],
    'T': [T, T.extract_signatures()[0].matrix_generator()],
    'CNOT': [CNOT, CNOT.extract_signatures()[0].matrix_generator()],
    'CCNOT': [CCNOT, CCNOT.extract_signatures()[0].matrix_generator()],
    'CSIGN': [CSIGN, CSIGN.extract_signatures()[0].matrix_generator()],
    'SWAP': [SWAP, SWAP.extract_signatures()[0].matrix_generator()],
    'SQRTSWAP':
    [SQRTSWAP, SQRTSWAP.extract_signatures()[0].matrix_generator()],
    'ISWAP': [ISWAP, ISWAP.extract_signatures()[0].matrix_generator()],
    'RX': [RX, RX.matrix_generator],
    'RY': [RY, RY.matrix_generator],
    'RZ': [RZ, RZ.matrix_generator],
    'PH': [PH, PH.matrix_generator],
}


def get_np_matrix_for_gate(
    gate: 'Gate', variables: Sequence[Union[int, float, 'Variable']] = ()
) -> np.array:
    matrix = get_np_matrix_from_standard_gates(gate.name)
    if matrix is not None:
        return matrix
    matrix = get_np_matrix_from_generator(gate, variables)
    return matrix


def get_np_matrix_from_standard_gates(gate_name: str) -> Optional[np.array]:
    try:
        return get_predef_generator()[gate_name]
    except KeyError:
        try:
            return get_param_generator()[gate_name]
        except KeyError:
            return None


def get_np_matrix_from_generator(
    gate: Union[AbstractGate, ParamGate],
    variables: Sequence[Union[int, float, 'Variable']] = ()
) -> np.array:
    if isinstance(gate, ParamGate):
        agate = gate.abstract_gate
    elif isinstance(gate, AbstractGate):
        agate = gate
    else:
        raise Exception("Only Param or Abstract gate accepted")
    return agate.matrix_generator(*variables)


def get_np_matrix_from_circuit(circuit: 'Circuit', gate_name: str):
    gate_def = circuit.gateDic[gate_name]
    gate_matrix_qlm = gate_def.matrix
    if gate_matrix_qlm is None:
        return None
    gate_matrix = mat2nparray(gate_matrix_qlm)
    return gate_matrix


def get_np_matrix_from_circuit_operation(circuit: 'Circuit', op: 'Op'):
    gate_name = op.gate
    matrix = get_np_matrix_from_circuit(circuit, gate_name)
    if matrix is None:
        gate, _ = get_gate_from_circuit_operation(circuit, op)
        matrix = generate_np_matrix_from_gate_signature(gate)
    return matrix


def get_paramgate_from_nparray(name: str, gate_matrix: np.array,
                               arity: int) -> Union[AbstractGate, ParamGate]:
    gate = AbstractGate(name, [],
                        matrix_generator=callback_matrix_lambda(gate_matrix),
                        arity=arity)
    return gate()


def get_paramgate_from_circuit_operation(
        circuit: 'Circuit', operation: 'Op') -> Union[AbstractGate, ParamGate]:
    gate_matrix = get_np_matrix_from_circuit_operation(circuit, operation)
    gate = get_paramgate_from_nparray(operation.gate, gate_matrix,
                                      len(operation.qbits))
    return gate


# Returns a gate and, if it depends on a variable (f.e. parametrized gates) the
# name of that variable
def get_gate_from_circuit_operation(
        circuit: 'Circuit',
        operation: 'Op') -> Tuple['Gate', Dict[str, 'Variable']]:
    name = operation.gate
    tup = get_gate_from_gate_name(circuit, name)
    if tup is None or tup[0] is None:
        # This fails (???) if the circuit has been generated without
        # submatrices
        gate_matrix = get_np_matrix_from_circuit_operation(circuit, operation)
        gate = get_paramgate_from_nparray(operation.gate, gate_matrix,
                                          len(operation.qbits))
        tup = (gate, {})
    return tup


def get_gate_from_gate_name(
        circuit: 'Circuit',
        name: str) -> Tuple[Union[None, 'Gate'], Dict[str, 'Variable']]:
    LOGGER.debug("name is %s", name)
    vname_to_var = {}
    if name.startswith("_"):
        # a. = Parametrized (RX, RY, RZ, PH) or user-defined gate
        gatedef = circuit.gateDic[name]
        syntax = gatedef.syntax
        if syntax is not None:
            # b. = a. + no ctrl(), dag(), ... to apply
            # In other words, no need to check subgate
            if syntax.name in GATE_SET_QAT.keys():
                # b. +  parametrized gate
                gate = GATE_SET_QAT[syntax.name][0]
                for parameter in syntax.parameters:
                    if parameter.is_abstract is not None:
                        var = variables.get_variable_from_circuit(
                            circuit, parameter.string_p)
                        vname_to_var[parameter.string_p] = var
                        gate = gate(var)
                    elif parameter.double_p is not None:
                        gate = gate(parameter.double_p)
                    elif parameter.int_p is not None:
                        gate = gate(parameter.double_p)
            else:
                # b. + user defined
                return None, dict()
        else:
            # b. = a. + subgate
            if gatedef.subgate is not None:
                subname = gatedef.subgate
                LOGGER.debug("subname is %s", subname)
                gate, subvname_to_vars = get_gate_from_gate_name(
                    circuit, subname)
                if subvname_to_vars is not None:
                    vname_to_var.update(subvname_to_vars)

        if gate is not None:
            if gatedef.nbctrls is not None:
                print(gatedef.nbctrls)
                gate = gate.ctrl(gatedef.nbctrls)
            if gatedef.is_conj:
                gate = gate.conj()
            if gatedef.is_dag:
                gate = gate.dag()
            if gatedef.is_trans:
                gate = gate.trans()
    else:
        # standard gate
        gate = globals()[name]

    return gate, vname_to_var


def generate_np_matrix_from_gate_signature(gate: 'Gate'):
    if gate.name in GATE_SET_QAT:
        return GATE_SET_QAT[f'{gate.name}'][1]
    matrix = GATE_SET_QAT[f'{gate.subgate.name}'][1]
    if gate.nb_ctrls is not None:
        matrix = get_ctrl_from_matrix(matrix, gate.nb_ctrls)
    if gate.is_dag is not None:
        matrix = get_dagger_from_matrix(matrix)
    if gate.is_conj is not None:
        matrix = get_conjugate_from_matrix(matrix)
    if gate.is_trans is not None:
        matrix = get_transpose_from_matrix(matrix)
    return matrix


# from myqlm
def mat2nparray(matrix):
    A = np.zeros((matrix.nRows, matrix.nCols), dtype=np.complex256)
    for cnt, (i, j) in enumerate(
            itertools.product(range(matrix.nRows), range(matrix.nCols))):
        A[i, j] = matrix.data[cnt].re + 1j * matrix.data[cnt].im
    return A


def extend_default_gate_set_from_custom_gates(
        gates: Sequence[Union[AbstractGate, ParamGate,
                              QRoutine]]) -> 'GateSet':
    gds = default_gate_set()
    signatures = []
    for gate in gates:
        if isinstance(gate, AbstractGate):
            signatures.append(gate)
        elif isinstance(gate, ParamGate):
            signatures.append(gate.abstract_gate)
        elif isinstance(gate, QRoutine):
            gds.union(extend_default_gate_set_from_custom_gates(gate))
        else:
            raise Exception(f"Gate of type {type(gate)} not acceptable")
    gds.union(generate_gate_set(*signatures))
    return gds


def generate_gate_set_from_abstract_gates(
        abstract_gates: Sequence[AbstractGate]) -> 'GateSet':
    return generate_gate_set(*abstract_gates)


def extract_custom_gates_from_program(
        program: 'Program') -> Sequence['AbstractGate']:
    lst = []
    for op in program.op_list:
        if op.gate.name not in GATE_SET_QAT:
            if isinstance(op.gate, AbstractGate):
                lst.append(op.gate)
            elif isinstance(op.gate, ParamGate):
                lst.append(op.gate.abstract_gate)
            elif isinstance(op.gate, QRoutine):
                lst.extend(extract_custom_gates_from_program(op.gate))
            else:
                raise Exception(f"Gate of type {type(op.gate)} not acceptable")
    return lst


def callback_matrix_lambda(matrix: np.array):
    return lambda: matrix
