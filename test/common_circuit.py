import logging
import os
# from collections import namedtuple
from test.common import BasicTestCase
from typing import TYPE_CHECKING

from qat.core.console import display
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import RProgram

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit
    from qat.core.wrappers.result import Result
    from qat.lang.AQASM.program import Program

LOGGER = logging.getLogger(__name__)


class CircuitTestCase(BasicTestCase):
    SLOW_TEST_ON = os.getenv("SLOW_ON") is not None
    SLOW_TEST_ON_REASON = "slow test"
    QLM_ON = os.getenv("QLM_ON") is not None
    QLM_ON_REASON = "not using qlm"
    if QLM_ON:
        SIMULATOR = os.getenv("SIMULATOR", "linalg")
    else:
        SIMULATOR = os.getenv("SIMULATOR", "pylinalg")
    # Try to use reversible simulator whenever possible
    REVERSIBLE_ON = os.getenv("REVERSIBLE_ON") is not None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.logger.info("using simulator: ")
        cls.links = []
        if cls.SIMULATOR.lower() == "pylinalg":
            cls.logger.info("PyLinalg")
            from qat.pylinalg import PyLinalg  # type:ignore

            cls.qpu = PyLinalg()
        elif cls.SIMULATOR.lower() == "linalg":
            # default to linalg
            from qat.qpus import LinAlg  # type:ignore

            cls.logger.info("LinAlg")
            cls.qpu = LinAlg()
        elif cls.SIMULATOR.lower() == "stabs":
            cls.logger.info("Stabs")
            from qat.qpus import Stabs  # type:ignore
            from qatext.synthesis.mctrls.mcx import ccnot, x

            cls.qpu = Stabs()
            cls.links = [ccnot, x]
        elif cls.SIMULATOR.lower() == "feynman":
            cls.logger.info("Feynman")
            from qat.qpus import Feynman  # type:ignore

            cls.qpu = Feynman()
        elif cls.SIMULATOR.lower() == "mps":
            cls.logger.info("MPS")
            from qat.qpus import MPS  # type:ignore

            cls.qpu = MPS(lnnize=True)
        elif cls.SIMULATOR.lower() == "bdd":
            cls.logger.info("BDD")
            from qat.qpus import Bdd  # type:ignore

            cls.qpu = Bdd(48)
        else:
            raise Exception(f"Simulator choice {cls.SIMULATOR} not correct")
        print(f"Selected simulator is {cls.qpu}")
        print(f"Reversible simulation is {cls.REVERSIBLE_ON}")

    @classmethod
    def simulate_program(cls, program, circ_args={}, job_args={}):
        if len(cls.links) > 0 and "link" not in circ_args:
            print("linking")
            circ_args["link"] = cls.links
        cr = program.to_circ(**circ_args)
        return cls.simulate_circuit(cr, job_args)

    @classmethod
    def simulate_circuit(cls, circuit, job_args={}):
        jb = circuit.to_job(**job_args)
        return cls.simulate_job(jb)

    @classmethod
    def simulate_job(cls, job):
        res = cls.qpu.submit(job)
        return res

    @staticmethod
    def draw_program(program: "Program", circ_kwargs={}, display_kwargs={}):
        cr = program.to_circ(**circ_kwargs)
        CircuitTestCase.draw_circuit(cr, **display_kwargs)

    @staticmethod
    def draw_circuit(circuit: "Circuit", **display_kwargs):
        display(circuit, **display_kwargs)

    @staticmethod
    def print_result(result: "Result"):
        for sample in result:
            print(sample)

    @classmethod
    def run_and_get_bitstring_for_reversible(cls, circ, reg_name_to_slice):
        """Circuit submission and result retrieval for a reversible simulator class."""
        if cls.REVERSIBLE_ON:
            rpr = RProgram.circuit_to_rprogram(circ, reg_name_to_slice)
            obtained = rpr.rbits.to01()
        else:
            res = cls.qpu.submit(circ.to_job())
            assert len(
                res) == 1, "Expected no. of results is 1, got %d" % len(res)
            sample = next(iter(res))
            if cls.SIMULATOR == "linalg":
                assert sample.probability == 1, "Expected probability is 1, got %f" % sample.probability
            obtained = sample.state.bitstring
        assert obtained is not None
        return obtained
