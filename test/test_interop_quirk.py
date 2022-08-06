from .common_circuit import CircuitTestCase
from parameterized import parameterized
from qat.external.interop.quirk import quirk
import unittest
import os
from typing import Callable, Dict, NamedTuple, Optional
import json

DATA_DIR = 'test/data/interop/quirk/'
FILE = DATA_DIR + '{filename}'


class QuirkCircData(NamedTuple):
    additional: str
    time_parameter: float
    circuit: str
    output_amplitude: str


class TestQuirk(CircuitTestCase):

    @classmethod
    def setUpClass(cls):
        cls.quirk_circ_datas = {}
        for fun_name in filter(
                lambda x: x.startswith('test') and callable(
                    getattr(TestQuirk, x)), dir(TestQuirk)):
            name = fun_name.split('test_')[1]
            cls.quirk_circ_datas[name] = cls._read_data(name)

        super().setUpClass()

    @classmethod
    def _read_data(cls, name) -> list[QuirkCircData]:
        # multiple names associated
        fnames = filter(lambda x: x.startswith(name), os.listdir(DATA_DIR))
        adds = []
        for fname in fnames:
            additional = fname.split(name)[1][1:]
            with open(FILE.format(filename=f"{name}_{additional}"), 'r') as f:
                data = json.loads(''.join(f.readlines()))
                quirkdata = QuirkCircData(additional, data['time_parameter'], data['circuit'],
                                          data['output_amplitudes'])
                adds.append(quirkdata)
        return adds

    def _test_common(self, fun_name: str):
        name = fun_name.split('test_')[1]
        for data in self.quirk_circ_datas[name]:
            with self.subTest(additional=data.additional):
                res_exp = quirk.simulation_data_list(data.output_amplitude)
                pr = quirk.dict_to_program(data.circuit)
                cr = quirk.convert_program_to_circuit(pr)
                jb = quirk.convert_circuit_to_job(cr, time_val=float(data.time_parameter))
                res = self.simulate_job(jb, )
                self._test_res(res_exp, res)

    def _test_res(self, res_exp_quirk, res_pr):
        for sample in res_pr:
            index = int(sample.state.bitstring[::-1], base=2)
            sample_exp = complex(res_exp_quirk[index])
            self.assertAlmostEqual(sample.amplitude, sample_exp)


    def test_init(self):
        self._test_common('test_init')

    def test_cols_simple(self):
        self._test_common('test_cols_simple')

    def test_cols_ctrls(self):
        self._test_common('test_cols_ctrls')

    def test_cols_zctrls(self):
        self._test_common('test_cols_zctrls')

    def test_formulaic_gates(self):
        # self.skipTest("Not yet")
        self._test_common('test_formulaic_gates')

    def test_custom_gates_matrix(self):
        self._test_common('test_custom_gates_matrix')

    def test_custom_gates_subcircuit(self):
        self.skipTest("Not yet")
        self._test_common('test_custom_gates_subcircuit')
