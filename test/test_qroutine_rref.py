import numpy as np
from test.common_circuit import CircuitTestCase
from parameterized import parameterized
from qat.external.utils.qroutines import rref
from qat.external.utils.qroutines import qregs_init
from qat.lang.AQASM.program import Program

from typing import List, Set, Tuple
from qat.core.console import display


class RrefTestCase(CircuitTestCase):
    def _prepare_circuit(self, matrix):
        self.pr = Program()
        n_rows, n_cols = matrix.shape
        self.qregs_rows = []
        for row_idx in range(n_rows):
            # qregs_rows.append(qregs_init.ini)
            qreg = self.pr.qalloc(n_cols)
            qrout = qregs_init.initialize_qureg_given_bitarray(
                matrix[row_idx, :], qreg, False)
            self.pr.apply(qrout, qreg)
            self.qregs_rows.append(qreg)

        self.qbit_range = set(q.index for qreg in self.qregs_rows
                              for q in qreg)

    @staticmethod
    def _build_from_result(res, qreg_range: Set[int], shape: Tuple[int, int]):
        # res = QPU.submit(prog.to_circ().to_job(qubits=rows_regs))
        # for sample in res:
        print(qreg_range)
        sample = res.raw_data[0]
        # print(sample.intermediate_measurements)
        print(sample.state)
        print(sample.state.bitstring)
        print(sample.state.value)

        matrix = np.zeros(shape, dtype=np.ubyte)
        print(f"shape is {shape}")
        interesting_bits = [
            val for i, val in enumerate(sample.state.bitstring)
            if i in qreg_range
        ]
        for i, val in enumerate(interesting_bits):
            row = i // shape[1]
            col = i % shape[0]
            matrix[row][col] = val

        print(matrix)

    def test_simple(self):
        matrix = np.array([[0, 1, 1], [1, 0, 1], [1, 0, 0]])
        matrix_list = matrix.tolist()
        print("original matrix")
        print(matrix)
        self._prepare_circuit(matrix)

        nrows, ncols = matrix.shape
        for i in range(nrows):
            agate = rref.get_row_swap(matrix_list, i)
            aoutn = len(range(i + 1, nrows))
            boutn = nrows - 1
            aout = self.pr.qalloc(aoutn)
            bout = self.pr.qalloc(boutn)
            bgate = rref.get_row_addition(matrix_list, i)
            print(f"Row {i}")
            print(f"qregs {[j for j in self.qregs_rows[i]]}")
            self.pr.apply(agate, *self.qregs_rows, aout)
            self.pr.apply(bgate, *self.qregs_rows, bout)
            print(f"Row {i} end")

        # display(self.pr.to_circ(), max_depth=3)
        print(self.pr.qbit_count)
        res = self.qpu.submit(self.pr.to_circ().to_job())
        self._build_from_result(res, self.qbit_range, matrix.shape)
