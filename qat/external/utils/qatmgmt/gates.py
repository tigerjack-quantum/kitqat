import itertools
import logging
from typing import TYPE_CHECKING

import numpy as np
from qat.lang.AQASM import (CCNOT, CNOT, CSIGN, ISWAP, PH, RX, RY, RZ,
                            SQRTSWAP, SWAP, AbstractGate, H, I, S, T, X, Y, Z)

if TYPE_CHECKING:
    from qat.lang.AQASM import (Circuit, Program, QRegister, Term, Gate, Qbit)
    from qat.comm.datamodel.ttypes import Op

LOGGER = logging.getLogger(__name__)

GATE_SET = {
    'H': [H, 1 / np.sqrt(2) * np.array([[1, 1], [1, -1]], dtype=complex)],
    'X': [X, np.array([[0, 1], [1, 0]])],
    'Y': [Y, np.array([[0, -1j], [1j, 0]], dtype=complex)],
    'Z': [Z, np.array([[1, 0], [0, -1]])],
    'I': [I, np.eye(2)],
    'S': [S, None],
    'T': [T, None],
    'CNOT': [
        CNOT,
        np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
                 dtype=complex)
    ],
    'CCNOT': [CCNOT, None],
    'CSIGN': [
        CSIGN,
        np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]],
                 dtype=complex)
    ],
    'SWAP':
    [SWAP,
     np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])],
    'SQRTSWAP': [
        SQRTSWAP,
        np.array([[1, 0, 0, 0], [0, .5 + .5j, .5 - .5j, 0],
                  [0, .5 - .5j, .5 + .5j, 0], [0, 0, 0, 1]])
    ],
    'ISWAP': [ISWAP, None],
    'RZ': [RZ, None],
    'RX': [RX, None],
    'RY': [RY, None],
    'PH': [PH, None]
}


def get_np_matrix_from_gate_name_default(gate_name: str):
    try:
        return GATE_SET[gate_name][1]
    except KeyError:
        return None


def get_np_matrix_from_gate_name(circuit: 'Circuit', gate_name: str):
    gate_def = circuit.gateDic[gate_name]
    gate_matrix_qlm = gate_def.matrix
    gate_matrix = mat2nparray(gate_matrix_qlm)
    return gate_matrix


def get_np_matrix_from_op(circuit: 'Circuit', op: 'Op'):
    gate_name = op.gate
    return get_np_matrix_from_gate_name(circuit, gate_name)


def get_abstractgate_from_nparray(name: str, gate_matrix: np.array,
                                  arity: int) -> AbstractGate:
    gate = AbstractGate(name, [],
                        matrix_generator=callback_matrix_lambda(gate_matrix),
                        arity=arity)
    return gate


def get_abstractgate_from_circuit_operation(circuit: 'Circuit',
                                            operation: 'Op') -> AbstractGate:
    gate_matrix = get_np_matrix_from_op(circuit, operation)
    gate = get_abstractgate_from_nparray(operation.gate, gate_matrix,
                                         len(operation.qbits))
    return gate


def get_gate_from_circuit_operation(circuit: 'Circuit',
                                    operation: 'Op') -> 'Gate':
    name = operation.gate
    gate = get_gate_from_gate_name(circuit, name)
    if gate is None:
        gate_matrix = get_np_matrix_from_op(circuit, operation)
        gate = get_abstractgate_from_nparray(operation.gate, gate_matrix,
                                             len(operation.qbits))()
    return gate


def get_gate_from_gate_name(circuit: 'Circuit', name: str) -> 'Gate':
    if name.startswith("_"):
        gatedef = circuit.gateDic[name]
        syntax = gatedef.syntax
        if syntax is not None:
            if syntax.name in GATE_SET.keys():
                # gate = globals()[syntax.name]
                gate = GATE_SET[syntax.name][0]
                for parameter in syntax.parameters:
                    gate = gate(parameter.double_p)
            else:
                return None
        else:
            if gatedef.subgate is not None:
                gate = gatedef.subgate
                gate = get_gate_from_gate_name(circuit, gate)
        if gatedef.is_conj:
            gate = gate.conj()
        if gatedef.is_dag:
            gate = gate.dag()
        if gatedef.is_trans:
            gate = gate.trans()
        if gatedef.nbctrls is not None:
            gate = gate.ctrl(gatedef.nbctrls)
    else:
        gate = globals()[name]
    return gate


# from myqlm
def mat2nparray(matrix):
    A = np.zeros((matrix.nRows, matrix.nCols), dtype=np.complex256)
    for cnt, (i, j) in enumerate(
            itertools.product(range(matrix.nRows), range(matrix.nCols))):
        A[i, j] = matrix.data[cnt].re + 1j * matrix.data[cnt].im
    return A


def callback_matrix_lambda(matrix: np.array):
    return lambda: matrix
