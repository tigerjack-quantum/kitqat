from itertools import combinations, product
from math import comb
from test.common_pytest import (REVERSIBLE_ON, REVERSIBLE_ON_REASON,
                                CircuitTestHelpers)

import pytest
from qat.lang.AQASM import classarith
from qat.lang.AQASM.program import Program
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import (RProgram, RSimulator)
from qatext.qroutines.arith import cuccaro_arith
from qatext.qroutines.qregs_mgmt.qregs_init import (
    initialize_qureg_given_bitstring, initialize_qureg_given_int)
from qatext.qroutines.walk.update_reversible0 import update_reversible


# class TestUpdate(CircuitTestHelpers):
#     def _get_neighbor(self, vertex, vertex_star, wstate_ones_str, wstate_zeros_str):
#         # find which elements to swap
#         remove_from_vertex      = vertex[wstate_ones_str.index('1')]       # 3
#         remove_from_vertex_star = vertex_star[wstate_zeros_str.index('1')] # 2

#         # perform the swap
#         vertex_new      = tuple(i for i in vertex      if i != remove_from_vertex) + (remove_from_vertex_star,)
#         vertex_star_new = tuple(i for i in vertex_star if i != remove_from_vertex_star) + (remove_from_vertex,)
#         return vertex_new, vertex_star_new

#     def _test_update_reversible_common_support(self, n, k,  vertex, vertex_star, wstate_ones_str, wstate_zeros_str):

#         m = (n-1).bit_length()
#         prw = ProgramWrapper(Program())
#         node_s_ones = prw.qarray_alloc(k, m, "s_1", int)
#         node_s_zeros = prw.qarray_alloc(n - k, m, "s_0", int)

#         node_t_ones = prw.qarray_alloc(k, m, "t_1", int)
#         node_t_zeros = prw.qarray_alloc(n - k, m, "t_0", int)

#         wstate_ones = prw.qarray_alloc(k, 1, "w_1", str)
#         wstate_zeros = prw.qarray_alloc(n - k, 1, "w_0", str)

#         # TODO temp, delete after
#         alpha_ones = prw.qarray_alloc(1, m, "a_1", int)
#         alpha_zeros = prw.qarray_alloc(1, m, "a_0", int)
#         qbit_out =  prw.qarray_alloc(1, 1, "out", bool)

#         prw.apply(initialize_qureg_given_bitstring(wstate_ones_str, False), wstate_ones)
#         prw.apply(initialize_qureg_given_bitstring(wstate_zeros_str, False), wstate_zeros)
#         # simulate_program(prw, True)

#         # dicke + bix ignored, just initialize them
#         for i, qreg in enumerate(node_s_ones):
#             qrout = initialize_qureg_given_int(vertex[i], m, False)
#             prw.apply(qrout, qreg)
#         for i, qreg in enumerate(node_s_zeros):
#             qrout = initialize_qureg_given_int(vertex_star[i], m, False)
#             prw.apply(qrout, qreg)

#         qrout = update_reversible(n, k, m, wstate_ones, wstate_zeros)
#         # prw.apply(qrout, node_s_ones, node_s_zeros, node_t_ones, node_t_zeros)
#         prw.apply(qrout, node_s_ones, node_s_zeros, node_t_ones, node_t_zeros, wstate_ones, wstate_zeros, alpha_ones, alpha_zeros, qbit_out)

#         name_to_values = RSimulator.simulate_and_decode(prw, link=[classarith, cuccaro_arith])
#         # circ = prw.to_circ(link=[classarith, cuccaro_arith], inline=True)
#         # # print(circ.depth(default=1))
#         # # convert quantum circuit from qat to reversible program
#         # rpr = RSimulator.from_circuit(circ)
#         # # ... and execute it
#         # rpr.apply_gates_from_circuit(circ, circ)
#         # # give the same name to the reversible program registers as the one in
#         # # program wrapper
#         # rpr.rregs = prw.get_name_to_qarray()
#         # # get the state (bistring) after applying the gate, divided by name of
#         # # the registers
#         # state = rpr.get_result_by_name()
#         # # convert the state into appropriate types (such as int, bool or str)
#         # name_to_values = RSimulator.decode_states(state, prw.get_name_to_qarray())

#         # name_to_values = RSimulator.simulate_and_decode(prw, link=[classarith, cuccaro_arith])
#         # print(name_to_values)
#         assert name_to_values['s_1'] == vertex, "s_1 not correctly initialized %s" % name_to_values["s_1"]
#         assert name_to_values['s_0'] == vertex_star, "s_0 not correctly initialized %s" % name_to_values["s_0"]

#         assert not any(s.any() for s in name_to_values['w_1'])
#         assert not any(s.any() for s in name_to_values['w_0'])

#         assert all(v == 0 for v in name_to_values['a_1']), "alpha_1 not zero %s" % name_to_values['a_1']
#         assert all(v == 0 for v in name_to_values['a_0']), "alpha_0 not zero %s" % name_to_values['a_0']

#         exp_t_ones, exp_t_zeros = self._get_neighbor(vertex, vertex_star, wstate_ones_str, wstate_zeros_str)

#         assert list(name_to_values['t_1']) == sorted(exp_t_ones)  #  , "t_1 not correctly initialized %s" % name_to_values["t_1"]
#         assert list(name_to_values['t_0']) == sorted(exp_t_zeros) #  , "t_0 not correctly initialized %s" % name_to_values["t_0"]

#     def _test_update_reversible_common(self, n, k, subtests):
#         # dic = defaultdict(set)

#         wstate_ones_combos = []
#         for c in combinations(range(k), 1):
#             combo = tuple("1" if j in c else "0" for j in range(k))
#             combo = "".join(combo)
#             wstate_ones_combos.append(combo)

#         wstate_zeros_combos = []
#         for c in combinations(range(n-k), 1):
#             combo = tuple("1" if j in c else "0" for j in range(n-k))
#             combo = "".join(combo)
#             wstate_zeros_combos.append(combo)

#         vertices = combinations(range(n), k)

#         for vertex in vertices:
#             vertex_star = tuple(i for i in range(n) if i not in vertex)
#             for wstate_ones_str, wstate_zeros_str in product(wstate_ones_combos, wstate_zeros_combos):
#                 with subtests.test(vertex=vertex, vertex_star=vertex_star, wstate_ones = wstate_ones_str, wstate_zeros = wstate_zeros_str):
#                     self._test_update_reversible_common_support(n, k, vertex, vertex_star, wstate_ones_str, wstate_zeros_str)

#     @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
#     @pytest.mark.parametrize(
#         "n, k",
#         [
#             (2, 1),
#             (3, 1),
#             (4, 1),
#             (4, 2),
#             (4, 3),
#             (5, 2),
#             (5, 3),
#             (6, 3),
#             (7, 2),
#         ],
#     )
#     def test_update_reversible(self, n, k, subtests):
#         self._test_update_reversible_common(n, k, subtests)


    # @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    # @pytest.mark.skipif(not SLOW_TEST_ON, reason=SLOW_TEST_ON_REASON)
    # @pytest.mark.parametrize(
    #     "n, k",
    #     [
    #         (8, 3),
    #         (8, 4),
    #         (9, 4),
    #         (10, 5),
    #     ],
    # )
    # def test_update_reversible_slow(self, n, k, subtests):
    #     self._test_update_reversible_common(n, k, subtests)
