from qat.external.utils.qroutines.hamming_weight_generate import bartschiE19


def go(n, k):
    (~bartschiE19.generate)(n, k)


def main():
    # n, r = 8192, 6528
    n, r = 4, 2
    # n, r = 7, 3
    go(n, r)


if __name__ == '__main__':
    main()
