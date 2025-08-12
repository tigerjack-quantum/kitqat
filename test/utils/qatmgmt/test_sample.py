from test.common_pytest import CircuitTestHelpers

import pytest
from qat.lang.AQASM.gates import H, X
from qat.lang.AQASM.program import Program
from qat.lang.AQASM.qbool import QBoolArray
from qat.lang.AQASM.qint import QInt
from qatext.utils.qatmgmt.sample import (extract_qreg_bitstring,
                                         extract_qreg_bitstrings_by_names,
                                         extract_qregs_bitstring,
                                         extract_qubit_bitstring)


class FakeQRegister:
    """Emulate a quantum register with startn and length"""

    def __init__(self, start, length):
        self.start = start
        self.length = length


class FakeState:

    def __init__(self, bitstring):
        self.bitstring = bitstring


class FakeSample:
    """Emulate a sample, each one having a bitstring and a state"""

    def __init__(self, qregs=None, amplitude=None, state=None):
        self.qregs = qregs
        self.state = state
        self.amplitude = amplitude


@pytest.mark.usefixtures("setup_simulator", "setup_logger")
class TestSample(CircuitTestHelpers):

    def _create_real_program(self):
        pr = Program()
        qreg0 = pr.qalloc(2, QInt)
        qreg1 = pr.qalloc(1, QBoolArray)
        qreg2 = pr.qalloc(1)

        pr.apply(H, qreg2)
        pr.apply(X.ctrl(), qreg2, qreg1)
        pr.apply(X.ctrl(), qreg2, qreg0[0])

        return pr, [qreg0, qreg1, qreg2]

    def test_extract_qreg_bitstring(self):
        qreg = FakeQRegister(start=2, length=3)
        state = FakeState("0101101")
        sample = FakeSample(qreg, None, state)
        result = extract_qreg_bitstring(qreg, sample)
        assert result == "011"

    def test_extract_qreg_bitstring_real(self):
        pr, qregs = self._create_real_program()
        res = self.simulate_program(pr)
        for sample in res:
            bits0 = extract_qreg_bitstring(qregs[0], sample)
            bits1 = extract_qreg_bitstring(qregs[1], sample)
            bits2 = extract_qreg_bitstring(qregs[2], sample)
            if bits2 == '0':
                assert bits1 == '0'
                assert bits0 == '00'
            else:
                assert bits1 == '1'
                assert bits0 == '10'

    def test_extract_qregs_bitstring(self):
        qregs = [FakeQRegister(0, 3), FakeQRegister(3, 2)]
        state = FakeState("0101101")
        sample = FakeSample(qregs, None, state)
        result = extract_qregs_bitstring(qregs, sample)
        assert result == ["010", "11"]

    def test_extract_qregs_bitstring_real(self):
        pr, qregs = self._create_real_program()
        res = self.simulate_program(pr)
        for sample in res:
            bitss = extract_qregs_bitstring(qregs, sample)
            if bitss[2] == '0':
                assert bitss == ['00', '0', '0']
            else:
                assert bitss == ['10', '1', '1']

    def test_extract_qreg_bitstrings_by_name(self):
        qregs = [FakeQRegister(0, 3), FakeQRegister(3, 2)]
        name_to_reg = {
            "first": qregs[0],
            "second": qregs[1],
        }
        state = FakeState("0101101")
        sample = FakeSample(qregs, None, state)
        result = extract_qreg_bitstrings_by_names(name_to_reg, sample)
        assert result == {
            "first": "010",
            "second": "11",
        }

    def test_extract_qreg_bitstrings_by_name_real(self):
        pr, qregs = self._create_real_program()
        name_to_reg = {
            "first": qregs[0],
            "second": qregs[1],
            "third": qregs[2],
        }
        res = self.simulate_program(pr)
        for sample in res:
            result = extract_qreg_bitstrings_by_names(name_to_reg, sample)
            if result['third'] == '0':
                assert result == {
                    "first": "00",
                    "second": "0",
                    "third": "0",
                }
            else:
                assert result == {
                    "first": "10",
                    "second": "1",
                    "third": "1",
                }

    @pytest.mark.parametrize(
        "qbit_idxs,bitstring,expected",
        [
            ([0, 2, 4], "0101101", "001"),
            ([1, 3], "0101101", "11"),
            ([], "0101101", ""),
        ],
    )
    def test_extract_qubit_bitstring(self, qbit_idxs, bitstring, expected):
        state = FakeState(bitstring)
        sample = FakeSample(None, None, state)
        result = extract_qubit_bitstring(qbit_idxs, sample)
        assert result == expected

    @pytest.mark.parametrize(
        "qbit_idxs",
        [
            ([0, 2, 3]),
            ([1, 3]),
            ([]),
        ],
    )
    def test_extract_qubit_bitstring_real(self, qbit_idxs):
        pr, qregs = self._create_real_program()
        res = self.simulate_program(pr)
        res_exp = ['0000', '1011']
        for sample in res:
            bits2 = extract_qreg_bitstring(qregs[2], sample)
            if bits2 == '0':
                result = extract_qubit_bitstring(qbit_idxs, sample)
                assert result == ''.join([res_exp[0][i] for i in qbit_idxs])
            else:
                result = extract_qubit_bitstring(qbit_idxs, sample)
                assert result == ''.join([res_exp[1][i] for i in qbit_idxs])
