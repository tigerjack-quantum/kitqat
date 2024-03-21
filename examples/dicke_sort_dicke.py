from qatext.qroutines.hamming_weight_generate import bartschiE19
from qat.core.console import display
from qat.lang.AQASM import Program

from qat.qpus import PyLinalg
from math import factorial

from qatext.qroutines import sorting_network as sn


def main():
    n = 4
    k = 2
    w = 2
    pr = Program()
    qr = pr.qalloc(n)
    pr.apply(bartschiE19.generate(n, w), qr)
    # display(pr.to_circ(), max_depth=3)
    exp_states = factorial(n) // (factorial(w) * factorial(n - w))
    print(f"Expected states: {exp_states}")

    # data = sn.get_pattern_sorter(n)
    # lines = pr.qalloc(data['n_lines'])
    # comps = pr.qalloc(data['n_comps'])

    # sort_net = sn.build_gate_sorter(data)
    # # pr.apply(sort_net, lines, comps)
    # pr.apply(sort_net, qr, comps)

    # pr.apply(X, qr[0])
    # pr.apply(X, qr[1])
    qr2 = pr.qalloc(k)
    pr.apply(bartschiE19.generate(k, 1), qr2)

    qpu = PyLinalg()

    res = qpu.submit(pr.to_circ(submatrices_only=True).to_job())
    print(f"obtained: {len(res)}")
    for sample in res:
        print(f"state: {sample.state}, {sample.probability}")


if __name__ == '__main__':
    main()
