import os
import tempfile

CHP_BIN = "/home_local/simone/git_repos/aaronson-chp/chp.out"


def to_chp(aqasm_filepath: str, output_filepath: str):
    """
    Convert to Aaronson CHP stabilizer simulator
    """

    with open(aqasm_filepath, 'r') as inp:
        with open(output_filepath, 'w') as out:
            print("", file=out)
            print("#", file=out)
            for line in inp.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                elif line.startswith('BEGIN') or line.startswith(
                        'qubits') or line.startswith('cbits'):
                    continue
                elif line.startswith('END'):
                    break
                st = _clean_gate(line)
                print(st, file=out)


def _clean_gate(inline):
    line = ""
    if inline.startswith('H'):
        line += "h "
        qubits = inline.split('H ')[1]
    elif inline.startswith('CNOT'):
        line += "c "
        qubits = inline.split('CNOT ')[1]
    elif inline.startswith('S'):
        line += "p "
        qubits = inline.split('S ')[1]
    elif inline.startswith('MEAS '):
        qubits = inline.split('MEAS ')[1]
        qubits = qubits.split('c')[0]
    else:
        print(inline)
        raise Exception("Unrecognized gate,")

    qubits = qubits.replace("q", "").replace("[",
                                             "").replace("]",
                                                         "").replace(",", " ")
    if inline.startswith('MEAS '):
        lines = [f"m {i}" for i in qubits if i.isdigit()]
        return '\n'.join(lines)
    else:
        return line + qubits


def simulate_chp(chp_file: str):
    fd, path = tempfile.mkstemp()

    os.system(f'{CHP_BIN} {chp_file} > {path}')
    # os.close(fd)
    try:
        with os.fdopen(fd, 'r') as tmp:
            lines = tmp.readlines()[4:]
    finally:
        print("removing")
        os.remove(path)

    # assume that the results are put in order
    results =  type('', (), {})()
    n_bits = len(lines)

    results.raw_data = []
    sample =  type('', (), {})()
    sample.state =  type('', (), {})()
    sample.state.bitstring = [None] * n_bits
    for val in map(
            lambda x: x.split(': '),
            map(lambda x: x.strip('Outcome of measuring qubit '),
                map(str.strip, lines))):
        sample.state.bitstring[int(val[0])] = val[1]

    sample.state.bitstring = ''.join(sample.state.bitstring)
    results.raw_data.append(sample)
    return results

