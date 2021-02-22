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
        print("using simulator: ", end="")
        if cls.QLM_ON == '0':
            print("PyLinalg")
            from qat.qpus import PyLinalg
            cls.qpu = PyLinalg()
        else:
            if cls.QLM_ON.lower() == 'stabs':
                print("Stabs")
                from qat.qpus import Stabs
                from qat.external.utils.mcx import ccnot
                cls.qpu = Stabs()
                cls.links = [ccnot]
            elif cls.QLM_ON.lower() == 'feynman':
                print("Feynman")
                from qat.qpus import Feynman
                cls.qpu = Feynman()
                cls.links = []
            elif cls.QLM_ON.lower() == 'mps':
                print("MPS")
                from qat.qpus import MPS
                cls.qpu = MPS(lnnize=True)
                cls.links = []
            else:
                # default to linalg
                from qat.qpus import LinAlg
                cls.qpu = LinAlg()
                cls.links = []

    @classmethod
    def simulate_program(cls, program, circ_args={}, job_args={}):
        cr = program.to_circ(*circ_args)
        jb = cr.to_job(*job_args)
        res = cls.qpu.submit(jb)
        return res

    @staticmethod
    def draw_circuit(program: Union['Program', 'Circuit'], **kwargs):
        try:
            display(program)
        except AttributeError:
            display(program.to_circ(), **kwargs)

    @staticmethod
    def print_result(result: 'Result'):
        for sample in result:
            print(sample)
