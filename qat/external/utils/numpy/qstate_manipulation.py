import functools
import logging

import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from qat.lang.AQASM.bits import Qbit

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


def get_ctrl_from_matrix(gate_matrix: np.array, nctrls: int) -> np.array:
    assert len(gate_matrix.shape) == 2
    assert gate_matrix.shape[0] == gate_matrix.shape[1]
    arity = int(np.log2(gate_matrix.shape[0]))
    new_matrix = np.eye(2**(nctrls + arity), dtype=complex)
    new_matrix[2**(nctrls + arity) - 2**arity:2**(nctrls + arity),
               2**(nctrls + arity) - 2**arity:2**(nctrls +
                                                  arity)] = gate_matrix
    return new_matrix


def get_transpose_from_matrix(gate_matrix: np.array) -> np.array:
    return gate_matrix.T


def get_conjugate_from_matrix(gate_matrix: np.array) -> np.array:
    return gate_matrix.conj()


def get_dagger_from_matrix(gate_matrix: np.array) -> np.array:
    return gate_matrix.T.conj()


def get_start_state(n_qubits: int) -> np.array:
    shape = tuple([2 for _ in range(n_qubits)])
    state_vec = np.zeros(shape, dtype=np.complex128)
    state_vec[tuple([0 for _ in range(n_qubits)])] = 1
    return state_vec


def get_state_as_tensor(state_vec: np.array) -> np.array:
    n_qubits = int(np.log2(state_vec.shape[0]))
    return np.reshape(state_vec, tuple([2 for _ in range(n_qubits)]))


def get_state_as_vector(state, basis_state='') -> np.array:
    if len(basis_state) == 0:
        return np.reshape(state, 2**len(state.shape))
    else:
        basis_dec = int(basis_state, 2)
        return np.reshape(state, 2**len(state.shape))[basis_dec]


def get_vector_from_basis_bitstring(bitstring) -> np.array:
    # The bitstring should represent a basis vector
    state_vec = np.zeros(2**len(bitstring))
    basis_decimal = int(bitstring, 2)
    LOGGER.debug("bitstring = %s, decimal = %d", bitstring, basis_decimal)
    state_vec[basis_decimal] = 1
    return state_vec


def get_tensor_from_matrix(matrix: np.array) -> np.array:
    arity = int(np.log2(matrix.shape[0]))
    tensor = matrix.reshape(tuple([2 for _ in range(2 * arity)]))
    return tensor


def apply_matrix_to_tensor_state(start_state: np.array,
                                      gate_matrix: np.array, *qubits: 'Qbit'):
    # LOGGER.debug(f"matrix = {gate_matrix}")
    LOGGER.debug("qubits %s", qubits)
    arity = len(qubits)
    LOGGER.debug("arity = %d", arity)

    # reshape for easy application.
    tensor = gate_matrix.reshape(tuple([2 for _ in range(2 * arity)]))
    # LOGGER.debug(f"tensor = {tensor}")

    # axes for tensor dot: last indices of gate tensor.
    gate_axes = [k for k in range(arity, 2 * arity)]
    LOGGER.debug("gate axes = %s", gate_axes)

    # actual gate application
    state_vec = np.tensordot(tensor, start_state, axes=(gate_axes, qubits))
    # LOGGER.debug(f"state vector after tensordot is = {state_vec}")

    # moving axes back to correct positions
    state_vec = np.moveaxis(state_vec, range(len(qubits)), qubits)
    return state_vec


def is_unitary(gate_array: np.array) -> bool:
    return np.allclose(gate_array.dot(gate_array.T.conj()),
                       np.eye(gate_array.shape[0]))
