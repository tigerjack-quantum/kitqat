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
        if cls.QLM_ON == '0':
            from qat.qpus import PyLinalg
            cls.qpu = PyLinalg()
        else:
            from qat.qpus import LinAlg
            cls.qpu = LinAlg()

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
