import functools
import logging

import numpy as np

LOGGER = logging.getLogger(__name__)


# NOTE: kwargs should be theta, phi, lambd in this order
def get_partial_applications_to_general_matrix_generator(**kwargs):
    return functools.partial(get_most_general_gate_matrix_generator(),
                             **kwargs)


def get_most_general_gate_matrix_generator():
    return lambda theta, phi, lambd: np.array(
        [[
            np.exp(-1j * (phi + lambd) / 2) * np.cos(theta / 2), -np.exp(
                -1j * (phi - lambd) / 2) * np.sin(theta / 2)
        ],
         [
             np.exp(1j * (phi - lambd) / 2) * np.sin(theta / 2),
             np.exp(1j * (phi + lambd) / 2) * np.cos(theta / 2)
         ]])


def get_ctrl_from_matrix(gate_matrix):
    new_matrix = np.eye(4, dtype=complex)
    new_matrix[2:4, 2:4] = gate_matrix
    return new_matrix


def get_start_state(n_qubits: int):
    shape = tuple([2 for _ in range(n_qubits)])
    state_vec = np.zeros(shape, dtype=np.complex128)
    state_vec[tuple([0 for _ in range(n_qubits)])] = 1
    return state_vec


def get_state_as_tensor(state_vec: np.array):
    n_qubits = int(np.log2(state_vec.shape[0]))
    return np.reshape(state_vec, tuple([2 for _ in range(n_qubits)]))


def get_state_as_vector(state, basis_state=''):
    if len(basis_state) == 0:
        return np.reshape(state, 2**len(state.shape))
    else:
        basis_dec = int(basis_state, 2)
        return np.reshape(state, 2**len(state.shape))[basis_dec]


def get_vector_from_basis_bitstring(bitstring):
    # The bitstring should represent a basis vector
    state_vec = np.zeros(2**len(bitstring))
    basis_decimal = int(bitstring, 2)
    LOGGER.debug(f"bitstring = {bitstring}, decimal = {basis_decimal}")
    state_vec[basis_decimal] = 1
    return state_vec


def get_tensor_from_matrix(matrix):
    arity = int(np.log2(matrix.shape[0]))
    tensor = matrix.reshape(tuple([2 for _ in range(2 * arity)]))
    return tensor


def apply_gate_matrix_to_tensor_state(start_state, gate_matrix, *qubits):
    LOGGER.debug(f"matrix = {gate_matrix}")
    LOGGER.debug(f"qubits = {qubits}")
    arity = len(qubits)
    LOGGER.debug(f"arity = {arity}")

    # reshape for easy application.
    tensor = gate_matrix.reshape(tuple([2 for _ in range(2 * arity)]))
    LOGGER.debug(f"tensor = {tensor}")

    # axes for tensor dot: last indices of gate tensor.
    gate_axes = [k for k in range(arity, 2 * arity)]
    LOGGER.debug(f"gate axes = {gate_axes}")

    # actual gate application
    state_vec = np.tensordot(tensor, start_state, axes=(gate_axes, qubits))
    LOGGER.debug(f"state vector after tensordot is = {state_vec}")

    # moving axes back to correct positions
    state_vec = np.moveaxis(state_vec, range(len(qubits)), qubits)
    return state_vec


def is_unitary(gate_array):
    return np.allclose(gate_array.dot(gate_array.T.conj()),
                       np.eye(gate_array.shape[0]))
