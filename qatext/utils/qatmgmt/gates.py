# Main data structures used from circuit
# - circ.ops contains operations
#   + Operation -> name: str, qbits: list[int], type: int, cbits, formula, remap
# - circ.gateDic: dict[str, GateDefinition]
#   + str -> the gate name
#   + GateDefinition: contains all the standard gates(X, Y, ...)
#     and the user-defined gates (_0, _1, ...)->
#         name: str,
#         arity: int,
#         matrix: Matrix (you can convert to numpy object),
#         is_ctrl/dag/trans/cong: optional[bool]
#         subgate: optional[?]
#         syntax: GSyntax -> name: str, parameters: list[?]
#         nbctrls: optional[int]
#         circuit_implementation: optional[Subcircuit]
#             Subcircuit -> ops, ancillas: list[?], nbqbits

# It is mainly used by the qat-gatesplitter project

import itertools
import logging
from typing import TYPE_CHECKING, Sequence, Union

import numpy as np
from qat.core.circuit_builder.builder import default_gate_set
from qat.core.circuit_builder.matrix_util import (
    get_param_generator,
    get_predef_generator,
)
from qatext.utils.numpy.qstate_manipulation import (
    get_conjugate_from_matrix,
    get_ctrl_from_matrix,
    get_dagger_from_matrix,
    get_transpose_from_matrix,
)
from qatext.utils.qatmgmt import variables
from qat.lang.AQASM.gates import (
    CCNOT,
    CNOT,
    CSIGN,
    ISWAP,
    PH,
    RX,
    RY,
    RZ,
    SQRTSWAP,
    SWAP,
    AbstractGate,
    Gate,
    H,
    I,
    ParamGate,
    S,
    T,
    X,
    Y,
    Z,
)
from qat.lang.AQASM.misc import generate_gate_set
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.routines import QRoutine

if TYPE_CHECKING:
    from qat.comm.datamodel.ttypes import GateDefinition, Op, Subcircuit
    from qat.core.gate_set import GateSet
    from qat.core.variables import Variable
    from qat.core.wrappers.circuit import Circuit

LOGGER = logging.getLogger(__name__)

GATE_SET_QAT = default_gate_set().gate_signatures
GATE_SET_TO_GATE = {
    "H": H,
    "X": X,
    "Y": Y,
    "Z": Z,
    "I": I,
    "S": S,
    "T": T,
    "CNOT": CNOT,
    "CCNOT": CCNOT,
    "CSIGN": CSIGN,
    "SWAP": SWAP,
    "SQRTSWAP": SQRTSWAP,
    "ISWAP": ISWAP,
    "RX": RX,
    "RY": RY,
    "RZ": RZ,
    "PH": PH,
}


###
# Only fun taking Program as input
###
def extract_custom_gates_from_program(program: "Program") -> Sequence["AbstractGate"]:
    lst = []
    """Return a list of gates not belonging to the default gate set"""
    for op in program.op_list:
        if op.gate.name not in GATE_SET_QAT:
            if isinstance(op.gate, AbstractGate):
                lst.append(op.gate)
            elif isinstance(op.gate, ParamGate):
                lst.append(op.gate.abstract_gate)
            elif isinstance(op.gate, QRoutine):
                lst.extend(extract_custom_gates_from_program(op.gate))
            elif isinstance(op.gate, Gate):
                if isinstance(op.gate.subgate, AbstractGate):
                    lst.append(op.gate)
                elif isinstance(op.gate.subgate, ParamGate):
                    lst.append(op.gate.subgate.abstract_gate)
    return lst


###
# Direct conversion Circuit-> Program
###


def from_circuit_to_program(circ: "Circuit") -> Program:
    """Returns a program built starting from circuit operations."""
    pr = Program()
    pr_qregs = []
    all_qbits = []
    for qreg in circ.qregs:
        qr = pr.qalloc(qreg.length)
        pr_qregs.append(qr)
        all_qbits.extend(qreg)
    apply_gates_from_circuit(circ, circ, pr, all_qbits)
    return pr


def apply_gates_from_circuit(
    toplevel_circ: "Circuit",
    scanning_circ: Union["Circuit", "Subcircuit"],
    pr: Program,
    qbits: list[int],
):
    for op in scanning_circ.ops:
        gatename = op.gate
        subcirc = toplevel_circ.gateDic[gatename].circuit_implementation
        if subcirc is not None:
            apply_gates_from_circuit(toplevel_circ, subcirc, pr, qbits)
        else:
            g, _ = generate_gate_from_circuit_op(toplevel_circ, op, {})
            gate_qbits = [qbits[i] for i in op.qbits]
            pr.apply(g, gate_qbits)


###
# Gate extraction
###
def generate_gate_from_circuit_op(
    circuit: "Circuit",
    operation: "Op",
    variables_map: dict[str, "Variable"],
    generate_variables_if_missing=False,
    apply_gatedef_ops=True,
) -> tuple["Gate", dict[str, "Variable"]]:
    """Returns a gate and, if it depends on a variable (f.e. parametrized
    gates) the name of that variable.

    :param Circuit circuit: the top-level circuit
    :param Op operation: the operation of teh circuit
    :param dict[str, Variable] variables_map: a map of variable names

    :return the gate and the list of newly created variables
    """
    name = operation.gate
    try:
        tup = get_gate_from_gate_name(
            circuit,
            name,
            variables_map,
            generate_variables_if_missing,
            apply_gatedef_ops,
        )
        return tup
    except AttributeError:
        gate_matrix = generate_np_matrix_from_circuit_by_op(
            circuit, operation, variables_map
        )
        gate = build_paramgate_from_nparray(
            operation.gate, gate_matrix, len(operation.qbits)
        )
        tup = (gate, {})
    # if tup is None or tup[0] is None:
    #     # This fails (???) if the circuit has been generated without
    #     # submatrices
    #     # WARN: It can generates cicular recursion
    return tup


# The list of variables returned contains the newly generated variables
def get_gate_from_gate_name(
    circuit: "Circuit",
    name: str,
    variables_map: dict[str, "Variable"],
    generate_variables_if_missing=False,
    apply_gatedef_ops=True,
) -> tuple["Gate", dict[str, "Variable"]]:
    """Get a gate from its name inspecting all the relevant datastructures
    contained in the circuit.

    :param Circuit circuit: the top-level circuit
    :param str name: the name of the gate
    :param dict[str, Variable] variables_map: a map of variable names
    :param bool apply_gatedef_ops: specify if you want to apply all the final
    :param bool operations, like ctrl, dagger, conjugate and transpose
    """
    LOGGER.debug("name is %s", name)
    vname_to_var: dict[str, "Variable"] = {}
    if not name.startswith("_"):
        # standard gate
        # gate = globals()[name]
        gate = GATE_SET_TO_GATE[name]
        return gate, vname_to_var

    # a. = Parametrized (RX, RY, RZ, PH), Abstract or user-defined gate
    gatedef = circuit.gateDic[name]
    syntax = gatedef.syntax
    gate = None
    if syntax is not None:
        # b. = a. + no ctrl(), dag(), ... to apply
        # In other words, no need to check subgate
        if syntax.name in GATE_SET_QAT:
            # b. +  parametrized gate
            # gate = GATE_SET_QAT[syntax.name]
            gate = GATE_SET_TO_GATE[syntax.name]
            for parameter in syntax.parameters:
                if parameter.is_abstract:
                    if parameter.string_p in variables_map:
                        gate = gate(variables_map[parameter.string_p])
                    elif generate_variables_if_missing:
                        var = variables.generate_variable_from_circuit(
                            circuit, parameter.string_p
                        )
                        vname_to_var[parameter.string_p] = var
                        gate = gate(var)
                    else:
                        raise AttributeError("Unable to associate a variable")
                elif parameter.double_p is not None:
                    gate = gate(parameter.double_p)
                elif parameter.int_p is not None:
                    gate = gate(parameter.int_p)
                else:
                    raise AttributeError("Unknown flow")
        elif gatedef.circuit_implementation is not None:
            raise AttributeError("TODO subcircuit")
    else:
        # b. = a. + subgate
        if gatedef.subgate is not None:
            subname = gatedef.subgate
            LOGGER.debug("subname is %s", subname)
            gate, subvname_to_vars = get_gate_from_gate_name(
                circuit, subname, variables_map, generate_variables_if_missing
            )
            vname_to_var.update(subvname_to_vars)
        else:
            raise AttributeError("Unknown flow")
    if gate is None:
        raise AttributeError(f"Gate not found for {name}")

    # gate name is lost once you apply ctrls, conj, dag or tans
    if apply_gatedef_ops:
        if gatedef.nbctrls is not None:
            gate = gate.ctrl(gatedef.nbctrls)
        if gatedef.is_conj:
            gate = gate.conj()
        if gatedef.is_dag:
            gate = gate.dag()
        if gatedef.is_trans:
            gate = gate.trans()

    return gate, vname_to_var


###
# Build Parametrized gates
###
def callback_matrix_lambda(matrix: np.ndarray):
    return lambda: matrix


def build_paramgate_from_nparray(
    name: str, gate_matrix: np.ndarray, arity: int
) -> Union[AbstractGate, ParamGate]:
    gate = AbstractGate(
        name, [], matrix_generator=callback_matrix_lambda(gate_matrix), arity=arity
    )
    return gate()


def get_paramgate_from_circuit_op(
    circuit: "Circuit",
    operation: "Op",
    variables_map: dict[str, "Variable"],
) -> Union[AbstractGate, ParamGate]:
    gate_matrix = generate_np_matrix_from_circuit_by_op(
        circuit, operation, variables_map
    )
    gate = build_paramgate_from_nparray(
        operation.gate, gate_matrix, len(operation.qbits)
    )
    return gate


###
# np matrices
###
# from myqlm
def mat2nparray(matrix):
    A = np.zeros((matrix.nRows, matrix.nCols), dtype=np.complex256)
    for cnt, (i, j) in enumerate(
        itertools.product(range(matrix.nRows), range(matrix.nCols))
    ):
        A[i, j] = matrix.data[cnt].re + 1j * matrix.data[cnt].im
    return A


def get_np_matrix_from_gate_definition(
    gate: "GateDefinition", variables: Sequence[Union[int, float, "Variable"]] = ()
) -> np.ndarray:
    try:
        matrix = get_np_matrix_from_standard_gates(gate.name)
    except KeyError:
        try:
            matrix = get_np_matrix_from_standard_gates(gate.subgate.name)
        except KeyError:
            matrix = get_np_matrix_from_generator(gate, variables)
    if gate.nb_ctrls is not None:
        matrix = get_ctrl_from_matrix(matrix, gate.nb_ctrls)
    if gate.is_dag is not None:
        matrix = get_dagger_from_matrix(matrix)
    if gate.is_conj is not None:
        matrix = get_conjugate_from_matrix(matrix)
    if gate.is_trans is not None:
        matrix = get_transpose_from_matrix(matrix)
    return matrix


def get_np_matrix_from_standard_gates(gate_name: str) -> np.ndarray:
    try:
        return get_predef_generator()[gate_name]
    except KeyError:
        return get_param_generator()[gate_name]


def get_np_matrix_from_generator(
    gate: Union[AbstractGate, ParamGate],
    variables: Sequence[Union[int, float, "Variable"]] = (),
) -> np.ndarray:
    if isinstance(gate, ParamGate):
        agate = gate.abstract_gate
    elif isinstance(gate, AbstractGate):
        agate = gate
    else:
        raise AttributeError("Only Param or Abstract gate accepted")
    return agate.matrix_generator(*variables)


def get_np_matrix_from_circuit_by_op(circuit: "Circuit", operation: "Op") -> np.ndarray:
    return get_np_matrix_from_circuit_by_name(circuit, operation.gate)


def get_np_matrix_from_circuit_by_name(
    circuit: "Circuit", gate_name: str
) -> np.ndarray:
    """Return the matrix associated to a gate by looking at the circuit object.

    Raise an exception if the matrix is not found
    """
    gate_def = circuit.gateDic[gate_name]
    gate_matrix_qlm = gate_def.matrix
    if gate_matrix_qlm is None:
        raise AttributeError(
            "No np matrix in circuit, maybe you used include_matrices=False at circuit"
            " generation time?"
        )
    gate_matrix = mat2nparray(gate_matrix_qlm)
    return gate_matrix


def generate_np_matrix_from_circuit_by_op(
    circuit: "Circuit",
    op: "Op",
    variables_map: dict[str, "Variable"],
) -> np.ndarray:
    gate, _ = generate_gate_from_circuit_op(circuit, op, variables_map)
    matrix = get_np_matrix_from_gate_definition(gate)
    return matrix


###
# Get param gate
###


def extend_default_gate_set_from_custom_gates(
    gates: Sequence[Union[AbstractGate, ParamGate, QRoutine]]
) -> "GateSet":
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
            raise AttributeError(f"Gate of type {type(gate)} not acceptable")
    gds.union(generate_gate_set(*signatures))
    return gds


def generate_gate_set_from_abstract_gates(
    abstract_gates: Sequence[AbstractGate],
) -> "GateSet":
    return generate_gate_set(*abstract_gates)
