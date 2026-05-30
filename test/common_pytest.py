import logging
from os import getenv
from typing import TYPE_CHECKING, Optional

from qat.core.console import display
from qat.core.qpu.qpu import QPUHandler

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

SIMULATOR = getenv("SIMULATOR", "linalg" if QLM_ON else "clinalg")

LOGGER = logging.getLogger(__name__)

class CircuitTestHelpers:
    links = []
    # set from conftest
    _logger: Optional[logging.Logger] = None
    _qpu: Optional[QPUHandler] = None  # replace QPU with the actual type

    @property
    def qpu(self) -> QPUHandler:
        assert self._qpu is not None, "QPU not set — did conftest run?"
        return self._qpu

    @classmethod
    def set_qpu(cls, qpu: QPUHandler) -> None:
        cls._qpu = qpu  # set the private attribute, not the property

    @property
    def logger(self) -> logging.Logger:
        assert self._logger is not None, "Logger not set — did conftest run?"
        return self._logger

    @classmethod
    def set_logger(cls, logger: logging.Logger) -> None:
        cls._logger = logger


    @classmethod
    def simulate_program(cls, program, circ_args=None, links=None, job_args=None) -> "Result":
        circ_args = circ_args or {}
        job_args = job_args or {}

        if links and "link" not in circ_args:
            LOGGER.info("Linking custom gates...")
            circ_args["link"] = links

        circuit = program.to_circ(**circ_args)
        return cls.simulate_circuit(circuit, job_args)

    @classmethod
    def simulate_circuit(cls, circuit, job_args=None) -> "Result":
        job_args = job_args or {}
        job = circuit.to_job(**job_args)
        return cls.simulate_job(job)

    @classmethod
    def simulate_job(cls, job) -> "Result":
        assert cls._qpu is not None, "QPU has not been initialized"
        res = cls._qpu.submit(job)
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
