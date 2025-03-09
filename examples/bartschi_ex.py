from qat.core.console import display
from qat.lang.AQASM.program import Program
from qatext.qroutines.hamming_weight_generate import bartschiE19


def main():
    n = 4
    w = 2
    pr = Program()
    qr = pr.qalloc(n)
    pr.apply(bartschiE19.generate(n, w), qr)
    display(pr.to_circ(), max_depth=3)


if __name__ == '__main__':
    main()
