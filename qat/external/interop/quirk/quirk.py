import json
from typing import Any, Dict, List, Union
import urllib.parse
from qat.lang.AQASM.program import Program
from qat.lang.AQASM import gates
from qat.lang.AQASM.routines import QRoutine
import functools
from qat.external.interop.quirk import parse

IGNORED_GATES = ('Chance', 1, '•', '◦')


def url_to_program(url: str) -> Program:
    url_parsed = urllib.parse.urlparse(url)
    if not url_parsed.fragment or not url_parsed.fragment.startswith(
            'circuit='):
        raise ValueError(f'Circuit not present')
    circ = url_parsed.fragment.partition("circuit=")[2]
    circ = urllib.parse.unquote(circ)
    return json_to_program(circ)


def json_to_program(circ_str: str):
    circ_dict = json.loads(circ_str)
    return dict_to_program(circ_dict)

def dict_to_program(circ_dict: dict):
    if not circ_dict.keys() <= {'cols', 'gates', 'init'}:
        raise ValueError('Unrecognized Circuit JSON keys.')

    pr = Program()
    nqubits = 0
    if len(circ_dict['cols']) > 0:
        nqubits = functools.reduce(max, map(len, circ_dict['cols']))
    if 'init' in circ_dict:
        qfun_init = _init(circ_dict['init'])
        nqubits = max(nqubits, qfun_init.arity)
        qr = pr.qalloc(nqubits)
        pr.apply(qfun_init, qr[:qfun_init.arity])
    else:
        qr = pr.qalloc(nqubits)

    gate_name_to_qrout = {}
    if 'gates' in circ_dict:
        _gates(circ_dict['gates'], gate_name_to_qrout)

    if len(circ_dict['cols']) > 0:
        cols = _cols(circ_dict['cols'], gate_name_to_qrout)
        pr.apply(cols, qr)

    return pr


def _init(init_j: List[Union[str, int]]) -> QRoutine:
    qfun = QRoutine()

    for i, val in enumerate(init_j):
        state = init_j[i]
        if state == 0:
            pass
        elif state == 1:
            qfun.apply(gates.X, i)
        elif state == '+':
            qfun.apply(gates.H, i)
        elif state == '-':
            qfun.apply(gates.X, i)
            qfun.apply(gates.H, i)
        elif state == 'i':
            qfun.apply(gates.H, i)
            qfun.apply(gates.S, i)
        elif state == '-i':
            qfun.apply(gates.H, i)
            qfun.apply(gates.S.dag(), i)
        else:
            raise ValueError(f'Unrecognized init state: {state!r}')
    return qfun


def _gates(gates_j, gate_name_to_qrout):
    if not isinstance(gates_j, list):
        raise ValueError('"gates" JSON must be a list.')
    for custom_gate in gates_j:
        _register_custom_gate(custom_gate, gate_name_to_qrout)


def _get_gate(gate_id, additional_gates):
    if gate_id in IGNORED_GATES:
        return None
    if gate_id in gates.__dict__:
        gate = gates.__dict__[gate_id]
    elif gate_id in additional_gates:
        gate = additional_gates[gate_id]
    else:
        raise Exception("Gate not found")
    return gate


def _cols(cols_j, additional_gates=None):
    qfun = QRoutine()
    if not isinstance(cols_j, list):
        raise ValueError(
            f'Circuit JSON cols must be a list, got.\nJSON={cols_j}')
    for col in cols_j:
        ctrls = [i for i, v in enumerate(col) if v == '•']
        zctrls = [i for i, v in enumerate(col) if v == '◦']
        ctrls.extend(zctrls)
        has_ctrls = len(ctrls) > 0
        for i in zctrls:
            qfun.apply(gates.X, i)
        for i, gate_id in enumerate(col):
            gate = _get_gate(gate_id, additional_gates)
            if gate == None:
                continue
            # print(gate)
            if has_ctrls and gate_id != '•':
                qfun.apply(gate.ctrl(len(ctrls)), *ctrls, i)
            else:
                qfun.apply(gate, i)
        for i in zctrls:
            qfun.apply(gates.X, i)
    return qfun


def _register_custom_gate(gate_json: Dict, registry: Dict[str, Any]):
    if 'id' not in gate_json:
        raise ValueError(
            f'Custom gate json must have an id key.\nCustom gate json={gate_json!r}.'
        )
    identifier = gate_json['id']
    if identifier in registry:
        raise ValueError(
            f'Custom gate with duplicate identifier: {identifier}')

    if 'matrix' in gate_json and 'circuit' in gate_json:
        raise ValueError(
            f'Custom gate json cannot have both a matrix and a circuit.\n'
            f'Custom gate json={gate_json!r}.')

    qrout = QRoutine()
    name = gate_json['name']
    if 'matrix' in gate_json:
        matrix_s = gate_json['matrix']
        if not isinstance(matrix_s, str):
            raise ValueError(
                f'Custom gate matrix json must be a string.\nCustom gate json={gate_json!r}.'
            )
        gate = gates.AbstractGate(name, [], matrix_generator=lambda : parse.parse_matrix(matrix_s))
        registry[identifier] = gate()
    elif 'circuit' in gate_json:
        raise Exception("not yet implemented")
        pass
        # qrout

        # comp = _parse_cols_into_composite_cell(gate_json['circuit'], registry)
        # registry[identifier] = CellMaker(
        #     identifier=identifier,
        #     size=comp.height,
        #     maker=lambda args: comp.with_line_qubits_mapped_to(
        #         list(args.qubits)),
        # )

    else:
        raise ValueError(f'Custom gate json must have a matrix or a circuit.\n'
                         f'Custom gate json={gate_json!r}.')


def simulation_data(output_json: str):
    data = json.loads(output_json)
    if 'output_amplitudes' not in data:
        raise ValueError("Unable to reconstruct output without amplitudes")

    amps_json = data['output_amplitudes']
    return simulation_data_list(amps_json)

def simulation_data_list(amplitude_list: list):
    amps_rebuild = []

    for res in amplitude_list:
        res_c = complex(res['r'], res['i'])
        amps_rebuild.append(res_c)

    return amps_rebuild
