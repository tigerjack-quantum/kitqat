from qat.external.utils.qroutines.hamming_weight_generate import bartschiE19
from qat.lang.AQASM.program import Program
from qat.core.util import statistics
# from qat.core.console import display
# from qat.lang.aqasm.gates import paramgate
from qat.external.utils.synthesis.mctrls.mry2 import MRY

def _generate_program(n, k):
    pr = Program()
    qr = pr.qalloc(n)
    pr.apply(bartschiE19.generate(n, k), qr)
    return pr


def _analyse_res_abstract_gates(n, k, pr):
    """Assert that the number of gates of type i and ii are equal to the ones
    expected.

    The formula for the expected gates has been evaluated in my Dicke
    state presentation (in which k is denoted as w)
    """
    circ = pr.to_circ(keep=['_BARTSCHI_I', '_BARTSCHI_II'])
    stats = circ.statistics()
    bartschi_i_exp = n - 1
    bartschi_ii_exp = n * k - n + 1 - k**2 / 2 - k / 2
    gates = stats['gates']

    bartschi_i_real = gates.get('_BARTSCHI_I', 0)
    bartschi_ii_real = gates.get('_BARTSCHI_II', 0)
    assert bartschi_i_real == bartschi_i_exp
    assert bartschi_ii_real == bartschi_ii_exp


def _analyse_res_real_generic_gates(n, k, pr):
    """Assert that the number of real, generic gates are equal to the ones
    expected.

    The formula for the expected gates has been evaluated in my Dicke
    state presentation (in which k is denoted as w)
    """
    circ = pr.to_circ()
    stats = circ.statistics()
    gates = stats['gates']
    bartschi_i_exp = n - 1
    bartschi_ii_exp = n * k - n + 1 - k**2 / 2 - k / 2
    cnot_i_exp = bartschi_i_exp * 2
    cry_i_exp = bartschi_i_exp * 1

    cnot_ii_exp = bartschi_ii_exp * 2
    ccry_ii_exp = bartschi_ii_exp * 1

    cnot_exp = cnot_i_exp + cnot_ii_exp

    cnot_real = gates.get('CNOT', 0)
    cry_real = gates.get('C-RY', 0)
    ccry_real = gates.get('C-C-RY', 0)
    assert cnot_exp == cnot_real
    assert cry_i_exp == cry_real
    assert ccry_ii_exp == ccry_real

def _analyse_res_quick(n, k, pr):
    """Assert that the number of real gates (limited to CNOT and RY) are equal
    to the ones expected.

    The formula for the expected gates has been evaluated in my Dicke
    state presentation (in which k is denoted as w). The gate
    decomposition is shown in the same slides.
    """
    circ = pr.to_circ()
    # display(circ, max_depth=1)
    stats = statistics(circ)
    # print(stats)
    mod_stats = {}
    k = k if k < n / 2 else n - k
    print(f"n(k) = {n}, k(p) = {k}")
    cnot_i = 4
    ry_i = 2
    cnot_ii = 6
    ry_ii = 4

    exp_cnot_1 = (n - k) * (cnot_i + (k - 1) * cnot_ii)
    exp_cnot_2 = (k - 1) * (cnot_i + (k - 2) * 1 / 2 * cnot_ii)
    exp_ry_1 = (n - k) * (ry_i + (k - 1) * ry_ii)
    exp_ry_2 = (k - 1) * (ry_i + (k - 2) * 1 / 2 * ry_ii)

    exp_cnot_calc = exp_cnot_1 + exp_cnot_2
    exp_ry_calc = exp_ry_1 + exp_ry_2
    exp_cnot = (n - 1) * cnot_i + (k - 1) * (n - k / 2 - 1) * cnot_ii
    exp_ry = (n - 1) * ry_i + (k - 1) * (n - k / 2 - 1) * ry_ii
    assert exp_cnot == exp_cnot_calc
    assert exp_ry == exp_ry_calc

    exp_stats = {'X': k, 'CNOT': exp_cnot, 'RY': exp_ry}
    print(exp_stats)
    for k, v in stats['gates'].items():
        if k == 'C-RY':
            mod_stats['RY'] = mod_stats.get('RY', 0) + 2 * v
            mod_stats['CNOT'] = mod_stats.get('CNOT', 0) + 2 * v
        elif k == 'C-C-RY':
            mod_stats['RY'] = mod_stats.get('RY', 0) + 4 * v
            mod_stats['CNOT'] = mod_stats.get('CNOT', 0) + 4 * v
        elif v == 0:
            continue
        else:
            mod_stats[k] = v

    print(mod_stats)
    assert exp_cnot == mod_stats['CNOT'], f"{mod_stats['CNOT']} and {exp_cnot}"
    assert exp_ry == mod_stats['RY'], f"{mod_stats['RY']} and {exp_ry}"



def _analyse_res_quick_linking(n, k, pr):
    """Assert that the number of real gates (limited to CNOT and RY) are equal
    to the ones expected.

    The formula for the expected gates has been evaluated in my Dicke
    state presentation (in which k is denoted as w). The gate
    decomposition is shown in the same slides.
    """
    circ = pr.to_circ()
    stats = statistics(circ)
    print(stats)
    input()
    return
    gates = stats['gates']
    # print(stats)

    k = k if k < n / 2 else n - k
    print(f"n(k) = {n}, k(p) = {k}")

    bartschi_i_exp = n - 1
    bartschi_ii_exp = n * k - n + 1 - k**2 / 2 - k / 2

    cnot_i_expanded = 4
    ry_i_expanded = 2
    cnot_ii_expanded = 6
    ry_ii_expanded = 4

    cnot_exp_expanded = bartschi_i_exp * cnot_i_expanded + bartschi_ii_exp * cnot_ii_expanded
    ry_exp_expanded = bartschi_i_exp * ry_i_expanded + bartschi_ii_exp * ry_ii_expanded

    exp_cnot_1 = (n - k) * (cnot_i + (k - 1) * cnot_ii)
    exp_cnot_2 = (k - 1) * (cnot_i + (k - 2) * 1 / 2 * cnot_ii)
    exp_ry_1 = (n - k) * (ry_i + (k - 1) * ry_ii)
    exp_ry_2 = (k - 1) * (ry_i + (k - 2) * 1 / 2 * ry_ii)

    exp_cnot_calc = exp_cnot_1 + exp_cnot_2
    exp_ry_calc = exp_ry_1 + exp_ry_2
    exp_cnot = (n - 1) * cnot_i + (k - 1) * (n - k / 2 - 1) * cnot_ii
    exp_ry = (n - 1) * ry_i + (k - 1) * (n - k / 2 - 1) * ry_ii
    assert exp_cnot == exp_cnot_calc
    assert exp_ry == exp_ry_calc

    exp_stats = {'X': k, 'CNOT': exp_cnot, 'RY': exp_ry}
    print(exp_stats)
    for k, v in stats['gates'].items():
        if k == 'C-RY':
            mod_stats['RY'] = mod_stats.get('RY', 0) + 2 * v
            mod_stats['CNOT'] = mod_stats.get('CNOT', 0) + 2 * v
        elif k == 'C-C-RY':
            mod_stats['RY'] = mod_stats.get('RY', 0) + 4 * v
            mod_stats['CNOT'] = mod_stats.get('CNOT', 0) + 4 * v
        elif v == 0:
            continue
        else:
            mod_stats[k] = v

    print(mod_stats)
    assert exp_cnot == mod_stats['CNOT'], f"{mod_stats['CNOT']} and {exp_cnot}"
    assert exp_ry == mod_stats['RY'], f"{mod_stats['RY']} and {exp_ry}"


def main():
    for n in range(4, 16):
        for k in range(1, int(n / 2)):
            pr = _generate_program(n, k)
            _analyse_res_abstract_gates(n, k, pr)
            # _analyse_res_real_generic_gates(n, k, pr)
            # _analyse_res_extensive(n, k)
            # _analyse_res_quick(n, k, pr)
            print("----")


if __name__ == '__main__':
    main()
