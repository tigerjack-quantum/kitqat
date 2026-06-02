__authors__ = [
    "Simone Perriello <sperriello@proton.me>",
    "Alessandro Finazzi <alessandro2.finazzi@mail.polimi.it>",
]

import numpy as np
from kitqat.algorithms.qaa_utils import oracle, precise_grover_iterations
from kitqat.qatmgmt.program import ProgramWrapper
from kitqat.qatmgmt.result import bitstring_to_register_map
from qat.lang.AQASM.gates import H, X, Z
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.routines import QRoutine
from qat.myqlm_clinalg.qpu import CLinalg


def simulate(circuit, **job_params):
    job = circuit.to_job(amp_threshold=1e-3, **job_params)
    result = CLinalg().submit(job)
    result = sorted(filter(lambda x: x.probability > 1e-4, result),
                    key=lambda x: x.probability,
                    reverse=True)
    return result


def diffusion(n):
    routine = QRoutine()
    wires = routine.new_wires(n)

    with routine.compute():
        for wire in wires:
            routine.apply(H, wire)
        for wire in wires:
            routine.apply(X, wire)
    routine.apply(Z.ctrl(n - 1), wires)
    routine.uncompute()

    return routine


def grover(sol: str, to_simulate=True):
    """
    Example of the Grover algorithm
    """
    n = len(sol)

    program = ProgramWrapper()
    wires = program.qarray_alloc(n, 1, "input", str)

    for wire in wires:
        program.apply(H, wire)

    nsteps = precise_grover_iterations(2**n)
    print(f"n iterations = {nsteps}")
    for _ in range(int(np.rint(nsteps))):
        program.apply(oracle(sol), wires)
        program.apply(diffusion(n), wires)

    circuit = program.to_circ(submatrices_only=True)
    print(circuit.statistics())
    print(f"Depth = {circuit.depth(default=1)}")

    if to_simulate:
        result = simulate(circuit)
        for sample in result:
            print(
                bitstring_to_register_map(sample.state.bitstring,
                                          program._name_to_qarray))
            # print(sample.state, sample.probability)


def main():
    sol = "110110101110"
    print("*" * 80)
    grover(sol)


if __name__ == "__main__":
    main()
