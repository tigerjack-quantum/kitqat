import functools
import json
import logging
import urllib.parse
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Union

import numpy as np
from qatext.interop.quirk import parse
from qatext.qroutines.qregs_mgmt import qregs_layout as ql
from qat.lang.AQASM import gates
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.routines import QRoutine

if TYPE_CHECKING:
    from qat.core.variables import Variable
    from qat.lang.AQASM.gates import ParamGate

LOGGER = logging.getLogger(__name__)

IGNORED_GATES = (1, "•", "◦", "Density", "Bloch", "Chance", "Amps")
TIME_GATES = {
    "Rxft",
    "Ryft",
    "Rzft",
    "X^ft",
    "Y^ft",
    "Z^ft",  #
    "X^½",
    "X^-½",
    "X^¼",
    "X^-¼",
    "Y^½",
    "Y^-½",
    "Y^¼",
    "Y^-¼",  #
    "X^t",
    "Y^t",
    "Z^t",
    "X^-t",
    "Y^-t",
    "Z^-t",
}


class PauliInfos(NamedTuple):
    matrix: np.ndarray
    # eigenvalues: np.ndarray
    # eigenvalues are always np.array([1, np.exp(-1j * np.pi)]),
    eigenv_plus: np.ndarray
    eigenv_minus: np.ndarray


PAULI_TO_NP = {
    "X": PauliInfos(
        np.array([[0, 1], [1, 0]]),
        np.array([1 / np.sqrt(2), 1 / np.sqrt(2)]),
        np.array([1 / np.sqrt(2), -1 / np.sqrt(2)]),
    ),
    "Y": PauliInfos(
        np.array([[0, -1j], [1j, 0]]),
        np.array([1 / np.sqrt(2), 1j / np.sqrt(2)]),
        np.array([1 / np.sqrt(2), -1j / np.sqrt(2)]),
    ),
    "Z": PauliInfos(np.array([[1, 0], [0, -1]]), np.array([1, 0]), np.array([0, 1])),
}

OTHER_MAPS = {
    "Z^½": gates.S,
    "Z^-½": gates.S.dag(),
    "Z^¼": gates.T,
    "Z^-¼": gates.T.dag(),
}


def simulation_data(output_json: str):
    data = json.loads(output_json)
    if "output_amplitudes" not in data:
        raise ValueError("Unable to reconstruct output without amplitudes")

    amps_json = data["output_amplitudes"]
    return simulation_data_list(amps_json)


def simulation_data_list(amplitude_list: list):
    amps_rebuild = []

    for res in amplitude_list:
        res_c = complex(res["r"], res["i"])
        amps_rebuild.append(res_c)

    return amps_rebuild


def convert_program_to_circuit(program: Program, **kwargs):
    circ = program.to_circ(**kwargs)
    return circ


def convert_circuit_to_job(circuit, time_val=0.0):
    job = circuit.to_job()
    vars = job.get_variables()
    if len(vars) > 0:
        if len(vars) > 1:
            raise Exception("We expect at most 1 var called t")
        # Don't know why they use time_val*2 - 1, but that's it
        # https://github.com/Strilanc/Quirk/blob/5416d529d9b50c33f924a171eed06d09f3ba8b3a/src/gates/ParametrizedRotationGates.js#L350
        job = job(**{"t": time_val * 2 - 1})
    return job


def url_to_program(url: str) -> Program:
    url_parsed = urllib.parse.urlparse(url)
    if not url_parsed.fragment or not url_parsed.fragment.startswith("circuit="):
        raise ValueError(f"Circuit not present")
    circ = url_parsed.fragment.partition("circuit=")[2]
    circ = urllib.parse.unquote(circ)
    return json_to_program(circ)


def json_to_program(circ_str: str):
    circ_dict = json.loads(circ_str)
    return dict_to_program(circ_dict)


def dict_to_program(circ_dict: dict):
    if not circ_dict.keys() <= {"cols", "gates", "init"}:
        raise ValueError("Unrecognized Circuit JSON keys.")

    pr = Program()
    var = pr.new_var(float, "t")
    nqubits = 0
    if len(circ_dict["cols"]) > 0:
        nqubits = functools.reduce(max, map(len, circ_dict["cols"]))
    if "init" in circ_dict:
        qfun_init = _init(circ_dict["init"])
        nqubits = max(nqubits, qfun_init.arity)
        qr = pr.qalloc(nqubits)
        pr.apply(qfun_init, qr[: qfun_init.arity])
    else:
        qr = pr.qalloc(nqubits)

    gate_name_to_qrout = {}
    qfun = _dict_to_qfun(circ_dict, nqubits, var, gate_name_to_qrout)
    pr.apply(qfun, qr)
    return pr


def _dict_to_qfun(
    circ_dict: dict,
    nqubits: int,
    var: "Variable",
    gate_name_to_qrout: Dict[str, Union[QRoutine, "ParamGate"]],
) -> QRoutine:
    qfun = QRoutine()
    qr = qfun.new_wires(nqubits)

    if "gates" in circ_dict:
        _gates(circ_dict["gates"], gate_name_to_qrout)

    if len(circ_dict["cols"]) > 0:
        cols = _cols(circ_dict["cols"], var, gate_name_to_qrout)
        qfun.apply(cols, qr)

    return qfun


def _init(init_j: List[Union[str, int]]) -> QRoutine:
    qfun = QRoutine()

    for i, state in enumerate(init_j):
        if state == 0:
            pass
        elif state == 1:
            qfun.apply(gates.X, i)
        elif state == "+":
            qfun.apply(gates.H, i)
        elif state == "-":
            qfun.apply(gates.X, i)
            qfun.apply(gates.H, i)
        elif state == "i":
            qfun.apply(gates.H, i)
            qfun.apply(gates.S, i)
        elif state == "-i":
            qfun.apply(gates.H, i)
            qfun.apply(gates.S.dag(), i)
        else:
            raise ValueError(f"Unrecognized init state: {state!r}")
    return qfun


def _gates(gates_j, gate_name_to_qrout):
    if not isinstance(gates_j, list):
        raise ValueError('"gates" JSON must be a list.')
    for custom_gate in gates_j:
        LOGGER.debug("Custom gate %s" % custom_gate)
        _register_custom_gate(custom_gate, gate_name_to_qrout)


def _register_custom_gate(gate_json: Dict, registry: Dict[str, Any]):
    if "id" not in gate_json:
        raise ValueError(
            f"Custom gate json must have an id key.\nCustom gate json={gate_json!r}."
        )
    identifier = gate_json["id"]
    if identifier in registry:
        raise ValueError(f"Custom gate with duplicate identifier: {identifier}")

    if "matrix" in gate_json and "circuit" in gate_json:
        raise ValueError(
            "Custom gate json cannot have both a matrix and a circuit.\n"
            f"Custom gate json={gate_json!r}."
        )

    name = gate_json["name"]
    LOGGER.debug("Custom gate name = %s" % name)
    if "matrix" in gate_json:
        LOGGER.debug("Custom gate has matrix")
        matrix_s = gate_json["matrix"]
        if not isinstance(matrix_s, str):
            raise ValueError(
                "Custom gate matrix json must be a string.\nCustom gate"
                f" json={gate_json!r}."
            )
        LOGGER.debug("Custom gate name=%s matrix\n%s" % (name, matrix_s))
        gate = gates.AbstractGate(
            name, [], matrix_generator=lambda: parse.parse_matrix(matrix_s)
        )
        arity = np.log2(matrix_s.count("{") - 1)
        if not arity.is_integer():
            raise ValueError("Unknown error, found arity %f" % arity)
        gate.arity = int(arity)
        registry[identifier] = gate()
    elif "circuit" in gate_json:
        LOGGER.debug("Custom gate has circuit")
        circ_dict = gate_json["circuit"]
        if len(circ_dict["cols"]) > 0:
            nqubits = functools.reduce(max, map(len, circ_dict["cols"]))
            LOGGER.debug("Custom gate has %d nqubits" % nqubits)
        else:
            raise ValueError("Wrong, no cols")
        qfun = _dict_to_qfun(circ_dict, nqubits, None, registry)
        qfun.name = gate_json["name"]
        LOGGER.debug("Custom gate created %s\n" % qfun)
        registry[identifier] = qfun
    else:
        raise ValueError(
            "Custom gate json must have a matrix or a circuit.\n"
            f"Custom gate json={gate_json!r}."
        )


def _cols(cols_j, var, additional_gates=None):
    qfun = QRoutine()
    if not isinstance(cols_j, list):
        raise ValueError(f"Circuit JSON cols must be a list, got.\nJSON={cols_j}")

    for col_idx, col in enumerate(cols_j):
        ctrls = []
        zctrls = []
        swap_idxs = []
        for i, v in enumerate(col):
            if v == "•":
                ctrls.append(i)
            elif v == "◦":
                zctrls.append(i)
            elif v == "Swap":
                swap_idxs.append(i)

        for i in zctrls:
            qfun.apply(gates.X, i)
        ctrls.extend(zctrls)
        has_ctrls = len(ctrls) > 0

        for i, gate_pre in enumerate(col):
            LOGGER.debug(f"Parsing gate: col = {col_idx}, row = {i}, name = {gate_pre}")
            gate = _get_gate(gate_pre, additional_gates, var)
            if gate is None:
                LOGGER.debug("None gate returned for %s" % gate_pre)
                continue
            LOGGER.debug("Gate arity is %d " % gate.arity)
            if gate is gates.SWAP:
                if len(swap_idxs) > 0:
                    targets = tuple(swap_idxs)
                    swap_idxs = []
                else:
                    LOGGER.debug("Skipping, this gate has already been processed")
                    # we already processed this swap
                    continue
            else:
                targets = [qb for qb in range(i, i + gate.arity)]

            if has_ctrls and gate_pre != "•":
                LOGGER.debug(
                    f"Applying gate {gate} with ctrls {ctrls} and targets {targets}"
                )
                qfun.apply(gate.ctrl(len(ctrls)), ctrls, targets)
            else:
                LOGGER.debug(f"Applying gate {gate} with targets {targets}")
                # gate_list = [qb for qb in range(i, targets)]
                qfun.apply(gate, targets)
        for i in zctrls:
            qfun.apply(gates.X, i)
    return qfun


def _get_gate(gate_pre, additional_gates, var):
    if isinstance(gate_pre, int):
        if gate_pre == 1:
            return None
        else:
            raise Exception("Unknown gate %s" % gate_pre)
    elif isinstance(gate_pre, dict):
        # parametric gate with arg
        gate_id = gate_pre["id"]
        gate_arg = gate_pre["arg"] if gate_pre["arg"] else None
        gate = _get_abstrat_gate(gate_id, gate_arg, var)
    elif isinstance(gate_pre, str):
        gate_id = gate_pre
        if gate_id in IGNORED_GATES:
            return None
        if gate_id in TIME_GATES:
            gate = _get_abstrat_gate(gate_id, None, var)
        elif gate_id in OTHER_MAPS:
            gate = OTHER_MAPS[gate_id]
        elif gate_id.startswith("<<"):
            gate = ql.rotate(int(gate_id[2]), 1)
        elif gate_id == "Swap":
            gate = gates.__dict__["SWAP"]
        elif gate_id in gates.__dict__:
            gate = gates.__dict__[gate_id]
        elif gate_id in additional_gates:
            gate = additional_gates[gate_id]
        else:
            raise Exception("Gate not found %s" % gate_id)
    else:
        raise Exception("Gate of unknown type %s" % gate_pre)
    return gate


def _get_abstrat_gate(gate_id, gate_arg, var):
    # def rot_angle(angle, pauli_name):
    #     # I think this is valid for RX, RY, RZ,but ATM is unused
    #     # R_n (angle) = e^(-i * angle/2 * d_n), where d_n is the matrix of
    #     # pauli gate n, n in (X, Y, Z)

    #     # = cos(angle/2)*I - i * sin(angle/2)* d_n
    #     pauli_matrix = PAULI_TO_NP[pauli_name].matrix
    #     LOGGER.debug("Pauli matrix is\n%s" % pauli_matrix)
    #     return np.cos(angle) * np.eye(2) - 1j * np.cos(angle) * pauli_matrix

    # def rot_value(value, pauli_name):
    #     # Another way to look at it is R_d_n = -i * d_n
    #     # The -i global phase gate
    #     qfun = QRoutine()
    #     qfun.apply(gates.PH(-np.pi / 2), 0)
    #     qfun.apply(gates.X, 0)
    #     qfun.apply(gates.PH(-np.pi / 2), 0)
    #     qfun.apply(gates.X, 0)
    #     # The actual rotation
    #     rotation_gate = f'R{pauli_name.upper()}'
    #     gate = gates.__dict__[rotation_gate]
    #     qfun.apply(gate(value * np.pi), 0)
    #     return qfun

    def exp_value(value, pauli_name):
        pauli_eig_p = PAULI_TO_NP[pauli_name].eigenv_plus
        pauli_eig_m = PAULI_TO_NP[pauli_name].eigenv_minus
        plus = np.outer(pauli_eig_p, pauli_eig_p.conj())
        minus = np.outer(pauli_eig_m, pauli_eig_m.conj())
        # eigval_m = np.exp(1j * np.pi)
        # angle = (eigval_m)**value
        angle = np.exp(1j * value * np.pi)
        matrix = plus + minus * angle
        return matrix

    if gate_id in ("Rxft", "Ryft", "Rzft"):
        gate = gates.__dict__[gate_id[:2].upper()]
        if gate_arg is not None:
            arg = float(parse.parse_expr(gate_arg))
        else:
            # https://github.com/Strilanc/Quirk/blob/5416d529d9b50c33f924a171eed06d09f3ba8b3a/src/gates/ParametrizedRotationGates.js#L350
            arg = np.pi * var**2
        gate = gate(arg)

    elif gate_id[1] == "^":
        LOGGER.debug("Getting abstract gate for %s" % gate_id)
        if gate_arg is not None:
            LOGGER.debug(f"arg {gate_arg}")
            exp = float(parse.parse_expr(gate_arg))
            LOGGER.debug("Exponent is %f " % exp)
        elif gate_id[2:] in ("¼", "-¼", "½", "-½"):
            LOGGER.debug(f"fraction {gate_id[2:]}")
            exp = float(parse.parse_expr(gate_id[2:]))
            LOGGER.debug("Exponent is %f " % exp)
        elif gate_id[2:] in ("ft", "t", "-t"):
            LOGGER.debug("Predefined time function")
            raise Exception("Not sure how to circumvent the use of a variable")
            # exp = np.sin(var * np.pi)
            # sin function approximation
            # exp = 16 * var * (np.pi - var) / (5 * np.pi**2 - 4 * var *
            #                                   (np.pi - var))
        else:
            raise Exception("Exponent not found for gate %s" % gate_id)

        pauli_name = gate_id[0]
        gate = gates.AbstractGate(
            f"Exp", [float, str], matrix_generator=lambda x, y: exp_value(x, y)
        )
        gate.arity = 1
        gate = gate(exp, pauli_name)

        LOGGER.debug("Created gate %s" % (gate.name))
        LOGGER.debug(
            "Matrix should be\n%s" % np.around(exp_value(exp, pauli_name), decimals=6)
        )
    else:
        raise Exception("Other gates not implemented yet")
    return gate
