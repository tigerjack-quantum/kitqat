import os
from test.common import BasicTestCase
from typing import TYPE_CHECKING, Union

from qat.core.console import display

if TYPE_CHECKING:
    from qat.lang.AQASM import Program
    from qat.core import Circuit, Result


class CircuitTestCase(BasicTestCase):
    SLOW_TEST_ON = os.getenv('SLOW_ON') is not None
    SLOW_TEST_ON_REASON = "slow test"
    QLM_ON = os.getenv('QLM_ON', '0')
    QLM_ON_REASON = "using qlm"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.logger.info("using simulator: ", end="")
        cls.links = []
        if cls.QLM_ON == '0':
            cls.logger.info("PyLinalg")
            from qat.qpus import PyLinalg
            cls.qpu = PyLinalg()
        else:
            if cls.QLM_ON.lower() == 'stabs':
                cls.logger.info("Stabs")
                from qat.qpus import Stabs
                from qat.external.utils.synthesis.mctrls.mcx import ccnot, x
                cls.qpu = Stabs()
                cls.links = [ccnot, x]
            elif cls.QLM_ON.lower() == 'feynman':
                cls.logger.info("Feynman")
                from qat.qpus import Feynman
                cls.qpu = Feynman()
            elif cls.QLM_ON.lower() == 'mps':
                cls.logger.info("MPS")
                from qat.qpus import MPS
                cls.qpu = MPS(lnnize=True)
            else:
                # default to linalg
                from qat.qpus import LinAlg
                cls.logger.info("LinAlg")
                cls.qpu = LinAlg()

    @classmethod
    def simulate_program(cls, program, circ_args={}, job_args={}):
        if len(cls.links) > 0 and 'link' not in circ_args:
            print("linking")
            circ_args['link'] = cls.links
        cr = program.to_circ(**circ_args)
        jb = cr.to_job(**job_args)
        res = cls.qpu.submit(jb)
        # print("simulation over")
        return res

    @staticmethod
    def draw_program(program: 'Program', circ_kwargs={}, display_kwargs={}):
        cr = program.to_circ(**circ_kwargs)
        CircuitTestCase.draw_circuit(cr, **display_kwargs)

    @staticmethod
    def draw_circuit(circuit: 'Circuit', **display_kwargs):
        display(circuit, **display_kwargs)

    @staticmethod
    def print_result(result: 'Result'):
        for sample in result:
            print(sample)
