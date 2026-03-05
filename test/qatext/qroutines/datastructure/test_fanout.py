from math import floor, log2
import pytest
from qat.lang.AQASM.program import Program
from qatext.qatmgmt.program import ProgramWrapper
from qatext.qpus.reversible import RProgram, get_rprogram_regs_values_from_states, get_states_from_program_wrapper, inspect_state_reversible_program
from qatext.qroutines.datastructure.fanout import fanout
from qatext.qroutines.qregs_mgmt.qregs_init import initialize_qureg_given_bitstring, initialize_qureg_given_int
from qatext.utils.bits import conversion
from qatext.utils.bits.conversion import get_ints_from_bitarray
from test.common_pytest import (REVERSIBLE_ON, REVERSIBLE_ON_REASON,
                                CircuitTestHelpers)

class TestFanout(CircuitTestHelpers):

    @pytest.mark.parametrize(
        "bitstring, n",
        [
            ("0",  1),
            ("1",  3),
            ("01",  2),
            ("10",  4),
            ("101",  3),
            ("111",  5),
            ("1010",  2),
            # useful for depth
            ("1101",  4),
            ("1101",  8),
            ("1101",  16),
            ("1101",  32),
        ],
    )
    @pytest.mark.skipif(not REVERSIBLE_ON, reason=REVERSIBLE_ON_REASON)
    def test_fanout(self, bitstring, n):
        m = len(bitstring)

        prw = ProgramWrapper(Program())
        # you can use int here instead of string just to show the potential of
        # inspect_state_reversible_program or get_rprogram_values
        qval = prw.qarray_alloc(1, m, "Original", str)
        qarray = prw.qarray_alloc(n, m, "Clones", str)

        prw.apply(initialize_qureg_given_bitstring(bitstring, False), qval)

        prw.apply(fanout(n, m), qval, qarray)
        # cr = prw.to_circ()
        # cr = prw.to_circ(link=[], inline=True)
        # print(cr.depth(default=1))

        # Option 1
        # res = get_states_from_program_wrapper(prw, None)
        # print(res)
        # assert res['Original'].to01() == bitstring
        # assert res['Clones'].to01() == bitstring * n

        # Option 2, assert missing cause it's just to inspect
        # state_str = inspect_state_reversible_program(prw, [])
        # print(state_str)

        # Option 3
        # same as pr.to_circ()
        circ = prw.to_circ()
        # print(circ.depth(default=1))
        # convert quantum circuit from qat to reversible program
        rpr = RProgram.circuit_to_rprogram(circ)
        # ... and execute it
        rpr.apply_gates_from_circuit(circ, circ)
        # give the same name to the reversible program registers as the one in
        # program wrapper
        rpr.rregs = prw.get_name_to_qarray()
        # get the state (bistring) after applying the gate, divided by name of
        # the registers
        state = rpr.get_result_by_name()
        # convert the state into appropriate types (such as int, bool or str)
        name_to_values = get_rprogram_regs_values_from_states(state, prw.get_name_to_qarray())
        # print(name_to_values)
        assert name_to_values['Original'][0].to01() == bitstring, "Original not correctly initialized %s" % name_to_values["Original"]
        assert all(val.to01() == bitstring for val in name_to_values["Clones"]), "Clones are not equal %s" % name_to_values['Clones']





