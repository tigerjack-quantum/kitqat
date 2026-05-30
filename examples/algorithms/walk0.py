
from qatext.qpus.reversible import RSimulator
from itertools import combinations, product

from qat.lang.AQASM import classarith
from qat.lang.AQASM.program import Program
from qat.myqlm_clinalg.qpu import CLinalg
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qatmgmt.sample import extract_qarray_values_by_named_qarrays
from qatext.qroutines.arith import cuccaro_arith
from qatext.qroutines.qregs_mgmt.qregs_init import (
    initialize_qureg_given_bitstring, initialize_qureg_given_int)
from qatext.qroutines.walk.update_reversible0 import update_reversible

QPU = CLinalg()

def simulate_quantum(prw):
    print("Program qubits")
    for k, v in prw._name_to_qarray.items():
        print(k, v.slic)
    cr = prw.to_circ(link=[classarith, cuccaro_arith])
    print(cr.statistics())
    job = cr.to_job()
    print("Simulating...")
    res = QPU.submit(job)
    for sample in res:
        result = extract_qarray_values_by_named_qarrays(
            prw._name_to_qarray, sample)
        print(sample.amplitude, result)

def simulate_reversible(prw):
    # state_str = inspect_state_reversible_program(prw, [])
    state_str = RSimulator.inspect(
        prw, [classarith, cuccaro_arith])
    print(state_str)


def simulate_program(
    prw: ProgramWrapper,  # Program or Circuit
    rev,
):
    if rev:
        simulate_reversible(prw)
    else:
        simulate_quantum(prw)
    # job = cr.to_job(qubits=qubits)

def main(n,
         k,
         values: list[int],
         to_simulate=False,
         ):
    # Assuming no duplicates
    assert k <= n/2, "k should be le than n/2"
    # insert = insert_lw if insert_lw else insert_ld
    m = (n-1).bit_length()
    values = sorted(values)
    values_star = [i for i in range(n) if i not in values]

    print(
        f"Original: n {n}, k {k}, m {m}, values {values}, values* = {values_star}"
    )
    wstate_ones_combos = []
    for c in combinations(range(k), 1):
        combo = tuple("1" if j in c else "0" for j in range(k))
        combo = "".join(combo)
        wstate_ones_combos.append(combo)

    wstate_zeros_combos = []
    for c in combinations(range(n-k), 1):
        combo = tuple("1" if j in c else "0" for j in range(n-k))
        combo = "".join(combo)
        wstate_zeros_combos.append(combo)

    for wstate_ones_str, wstate_zeros_str in product(wstate_ones_combos, wstate_zeros_combos):
        print("****")
        print(wstate_ones_str, wstate_zeros_str)

        prw = ProgramWrapper(Program())
        node_s_ones = prw.qarray_alloc(k, m, "s_1", int)
        node_s_zeros = prw.qarray_alloc(n - k, m, "s_0", int)

        node_t_ones = prw.qarray_alloc(k, m, "t_1", int)
        node_t_zeros = prw.qarray_alloc(n - k, m, "t_0", int)

        wstate_ones = prw.qarray_alloc(k, 1, "w_1", str)
        wstate_zeros = prw.qarray_alloc(n - k, 1, "w_0", str)

        # TODO temp, delete after
        # alpha_ones = prw.qarray_alloc(1, m, "a_1", int)
        # alpha_zeros = prw.qarray_alloc(1, m, "a_0", int)
        # qbit_out =  prw.qarray_alloc(1, 1, "out", bool)
        #

        prw.apply(initialize_qureg_given_bitstring(wstate_ones_str, False), wstate_ones)
        prw.apply(initialize_qureg_given_bitstring(wstate_zeros_str, False), wstate_zeros)
        # simulate_program(prw, True)

        # dicke + bix ignored, just initialize them
        for i, qreg in enumerate(node_s_ones):
            qrout = initialize_qureg_given_int(values[i], m, False)
            prw.apply(qrout, qreg)
        for i, qreg in enumerate(node_s_zeros):
            qrout = initialize_qureg_given_int(values_star[i], m, False)
            prw.apply(qrout, qreg)

        # if to_simulate:
        #     simulate_program(prw)

        qrout = update_reversible(n, k, m, wstate_ones, wstate_zeros)
        # prw.apply(qrout, node_s_ones, node_s_zeros, node_t_ones, node_t_zeros)
        prw.apply(qrout, node_s_ones, node_s_zeros, node_t_ones, node_t_zeros, wstate_ones, wstate_zeros)

        if to_simulate:
            simulate_program(prw, True)

    # else:
    #     cr = prw.to_circ(link=[classarith, cuccaro_arith])
    #     print(cr.statistics())


    # len_w1 = k
    # len_w0 = (n - k)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("two boolean params: to_simulate, and intermediate_simulation")
    to_simulate = bool(sys.argv[1])
    # intermediate_simulation = bool(sys.argv[2])
    print(f"To simulate is {to_simulate}")
    values = [1, 3]
    n = 4
    k = 2
    # m = max(values).bit_length()
    ts = 1
    main(n,
         k,
         values,
         to_simulate=to_simulate,
         )
