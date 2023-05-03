from qat.lang.AQASM import H, Program

from qat.external.qroutines import qregs_init as qregs
from qat.external.qroutines.hamming_weight_compute import fpc
from qat.core.util import statistics
from qat.core.console import display

from math import log


def main():
    for i in range(2, 6):
        test_fpc_weight_compute(i)
        print("----")


def test_fpc_weight_compute(i):
    r = 2**i
    print(f"r = {r}")
    nwr_dict = fpc.get_qroutine_for_qubits_weight_get_pattern(r)
    print(f"ncouts, exp = {r - 1} real = {nwr_dict['n_couts']}")
    # self.logger.debug("nwr_dict %s", nwr_dict)
    program = Program()

    a = program.qalloc(nwr_dict['n_lines'])
    cout = program.qalloc(nwr_dict['n_couts'])

    # qfun = qregs.initialize_qureg_given_bitstring(name, a, True)
    # program.apply(qfun, a)

    qfun = fpc.get_qroutine_for_qubits_weight(len(a), len(cout), nwr_dict)
    program.apply(qfun, a, cout)
    print(f"bah {program.qbit_count}")
    circ = program.to_circ()

    # display(circ, max_depth = 0, circuit_name=f"{r}")
    orig_stats = statistics(circ)
    print(f"n_adders, expected {r -1}, real = {orig_stats['size']}")
    print(f"n_qubits, expected {2*r}, real = {circ.nbqbits}")

    # exp_x = 4*r - 2*i - 4 + r
    # exp_x = r/2 * 2 + ((2*r)*(2**(-i-1))*(-2*i + 3*(2**i) - 4))
    # exp_x = r/2 * 2 + (r*(2**(-i-2)))*(-2*i + 3*(2**i) - 4)
    exp_x = 9*r/2 - 2*i - 4
    # exp_cnot = 10*r - 5*i - 10
    # exp_cnot = r/2 + r*(5/2 - 5*(2**(-i)))
    exp_cnot = 35*r/4 - 5*i - 11
    # exp_ccnot = 4*r - 2*i - 4
    exp_ccnot = 7*r/2 - 2*i - 4
    # exp_ccnot = r/2 + r*(5/2 - 5*(2**-i))
    exp_gates = {'CNOT': exp_cnot, 'X': exp_x, 'CCNOT': exp_ccnot}

    new_stats = orig_stats['gates']
    new_stats.pop('custom gate')
    uma_cnot = int(new_stats['CCNOT'] /2)
    print(uma_cnot)
    new_stats['X'] += uma_cnot * 2
    new_stats['CNOT'] += uma_cnot
    print(f"expe = {exp_gates}")
    print(f"real = {new_stats}")




    # to_measure_qubits = fpc.get_to_measure_qubits(a, cout, nwr_dict)

    # res = self.qpu.submit(
    #     program.to_circ().to_job(qubits=[qb.index
    #                                      for qb in to_measure_qubits]))
    # self.logger.debug("res %s", res)

    # counts = len(res.raw_data)
    # self.assertEqual(counts, 1)
    # exp_w = name.count("1")
    # state = res.raw_data[0].state
    # self.assertEqual(state.lsb_int, exp_w)


if __name__ == '__main__':
    main()
