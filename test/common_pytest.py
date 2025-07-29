import logging
from os import getenv
from typing import TYPE_CHECKING, Optional

from qat.core.console import display

from qatext.qpus.reversible import RProgram

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit
    from qat.core.wrappers.result import Result
    from qat.lang.AQASM.program import Program

# Constants and flags
SLOW_TEST_ON = getenv("SLOW_ON") is not None
SLOW_TEST_ON_REASON = "slow test"

QLM_ON = getenv("QLM_ON") is not None
QLM_ON_REASON = "not using QLM"

REVERSIBLE_ON = getenv("REVERSIBLE_ON") is not None
REVERSIBLE_ON_REASON = "not using reversible simulator"

SIMULATOR = getenv("SIMULATOR", "linalg" if QLM_ON else "pylinalg")

LOGGER = logging.getLogger(__name__)


class CircuitTestHelpers:
    links = []
    qpu = None
    logger: Optional[logging.Logger] = None

    @classmethod
    def simulate_program(cls, program, circ_args=None, links=None, job_args=None):
        circ_args = circ_args or {}
        job_args = job_args or {}

        if links and "link" not in circ_args:
            LOGGER.info("Linking custom gates...")
            circ_args["link"] = links

        circuit = program.to_circ(**circ_args)
        return cls.simulate_circuit(circuit, job_args)

    @classmethod
    def simulate_circuit(cls, circuit, job_args=None):
        job_args = job_args or {}
        job = circuit.to_job(**job_args)
        return cls.simulate_job(job)

    @classmethod
    def simulate_job(cls, job):
        assert cls.qpu is not None
        res = cls.qpu.submit(job)
        return res

    @staticmethod
    def draw_program(program: "Program", circ_kwargs={}, display_kwargs={}):
        cr = program.to_circ(**circ_kwargs)
        CircuitTestHelpers.draw_circuit(cr, **display_kwargs)

    @staticmethod
    def draw_circuit(circuit: "Circuit", **display_kwargs):
        display(circuit, **display_kwargs)

    @staticmethod
    def print_result(result: "Result"):
        for sample in result:
            print(sample)
