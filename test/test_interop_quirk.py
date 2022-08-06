from .common_circuit import CircuitTestCase
from parameterized import parameterized
from qat.external.interop import quirk
import unittest


class TestQuirk(CircuitTestCase):

    def _test_res(self, res_exp_quirk, res_pr):
        for sample in res_pr:
            index = int(sample.state.bitstring[::-1], base=2)
            # index = int(sample.state.state)
            sample_exp = complex(res_exp_quirk[index])
            self.assertAlmostEqual(sample.amplitude, sample_exp)

    def test_init(self):
        for init_val in (1, '+', '-', 'i', '-i'):
            with self.subTest(init_val=init_val):
                with open(f'test/data/interop/quirk/init_{init_val}_url'
                          ) as fin, open(
                              f'./test/data/interop/quirk/init_{init_val}_res'
                          ) as fres:
                    line = fin.readline()
                    pr = quirk.url_to_program(line)
                    res_exp = quirk.simulation_data(''.join(fres.readlines()))
                    res = self.simulate_program(pr)
                    self._test_res(res_exp, res)

    def test_cols_simple(self):
        circ_json = '{"cols": [["H", "X"]]}'
        circ_res = '{"output_amplitudes":[{"r":0,"i":0},{"r":0,"i":0},{"r":0.7071067690849304,"i":0},{"r":0.7071067690849304,"i":0}]}'
        res_exp = quirk.simulation_data(circ_res)
        pr = quirk.json_to_program(circ_json)
        res = self.simulate_program(pr)
        self._test_res(res_exp, res)


    def test_cols_ctrls(self):
        circ_url = 'https://algassert.com/quirk#circuit={%22cols%22:[[%22H%22,1,%22Z%22],[%22%E2%80%A2%22,%22Z%22,%22%E2%80%A2%22]],%22init%22:[%22-i%22]}'
        circ_res = '{"output_amplitudes":[{"r":0.4999999701976776,"i":-0.4999999701976776},{"r":0.4999999701976776,"i":0.4999999701976776},{"r":0,"i":0},{"r":0,"i":0},{"r":0,"i":0},{"r":0,"i":0},{"r":0,"i":0},{"r":0,"i":0}]}'
        res_exp = quirk.simulation_data(circ_res)
        pr = quirk.url_to_program(circ_url)
        self.draw_circuit(pr.to_circ())
        res = self.simulate_program(pr)
        self._test_res(res_exp, res)

    def test_cols_zctrls(self):
        circ_url = 'https://algassert.com/quirk#circuit={%22cols%22:[[%22H%22,1,%22Z%22],[%22%E2%97%A6%22,%22Z%22,%22%E2%80%A2%22]],%22init%22:[%22-i%22]}'
        circ_res = '{"output_amplitudes": [{"r":0.4999999701976776,"i":-0.4999999701976776},{"r":0.4999999701976776,"i":0.4999999701976776},{"r":0,"i":0},{"r":0,"i":0},{"r":0,"i":0},{"r":0,"i":0},{"r":0,"i":0},{"r":0,"i":0}]}'
        res_exp = quirk.simulation_data(circ_res)
        pr = quirk.url_to_program(circ_url)
        self.draw_circuit(pr.to_circ())
        res = self.simulate_program(pr)
        self._test_res(res_exp, res)

    def test_custom_gates(self):
        pass
        # circ_txt = (
        # '{"cols":[["~d3pq"],["Y"]],'
        # '"gates":[{"id":"~d3pq","circuit":{"cols":[["H"],["•","X"]]}}]}')
