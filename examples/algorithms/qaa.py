__authors__ = [
    "Simone Perriello <sperriello@proton.me>",
    "Alessandro Finazzi <alessandro2.finazzi@mail.polimi.it>",
]

import math

from kitqat.algorithms.qaa_utils import oracle, precise_grover_iterations
from kitqat.qroutines.hamming_weight_generate import bartschiE19
from kitqat.qroutines.rotation.flip_basis import flip_zero
from qat.lang.AQASM.program import Program
from qat.myqlm_clinalg.qpu import CLinalg


def simulate(circuit, **job_params):
    job = circuit.to_job(amp_threshold=1e-3, **job_params)
    result = CLinalg().submit(job)
    result = sorted(filter(lambda x: x.probability > 1e-4, result),
                    key=lambda x: x.probability,
                    reverse=True)
    return result


def qaa(n, sol, init_rout, init_rout_n_states, to_simulate=True):
    """Example of the Grov er algorithm

    """
    program = Program()
    wires = program.qalloc(n)
    program.apply(init_rout, wires)

    nsteps = precise_grover_iterations(init_rout_n_states)
    print(f"n iterations = {nsteps}")
    for _ in range(int(nsteps)):
        program.apply(oracle(sol), wires)
        # diffusion
        program.apply(init_rout.dag(), wires)
        program.apply(flip_zero(n), wires)
        program.apply(init_rout, wires)

    circuit = program.to_circ(submatrices_only=True,
                              include_matrices=to_simulate)
    print(circuit.statistics())
    print(f"Depth = {circuit.depth(default=1)}")

    if to_simulate:
        result = simulate(circuit)
        for sample in result:
            print(sample.state, sample.probability)


def main():
    sol = "11000000001100"
    print("*" * 80)
    n = len(sol)
    k = sol.count("1")
    init_routine = bartschiE19.generate(n, k)
    init_routine_n_states = math.comb(n, k)
    qaa(n, sol, init_routine, init_routine_n_states)


if __name__ == '__main__':
    main()
