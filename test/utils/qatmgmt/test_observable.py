from qat.core import Observable, Term
from qat.lang.AQASM import H, Program, X, Y, RX, QRoutine, RZ, RY, Z, CNOT
from qatext.utils.qatmgmt.observables import produce_term_gates
from qatext.utils.qatmgmt.results import get_sample_for_basis_str_from_res
from copy import deepcopy

from test.common_circuit import CircuitTestCase


class TestQatUtils(CircuitTestCase):
    def _compare_expvalue_to_splitter_res(self, qfun, observable):
        nbqbits = qfun.arity
        prog = Program()
        qbits = prog.qalloc(nbqbits)

        prog.apply(qfun, qbits)
        res = self.qpu.submit(
            prog.to_circ().to_job(job_type="OBS", observable=observable)
        )
        final_amp = observable.constant_coeff
        for term in observable.terms:
            prog2 = Program()
            qbits2 = prog2.qalloc(nbqbits)
            prog2.apply(qfun, qbits2)
            for qbidx, gates in produce_term_gates(term).items():
                for gate in gates:
                    prog2.apply(gate, qbits2[qbidx])
            prog2.apply(qfun.dag(), qbits2)
            from qat.core.console import display

            res2 = self.qpu.submit(prog2.to_circ().to_job())
            sample = get_sample_for_basis_str_from_res(res2, "0" * nbqbits)
            amp = term.coeff * sample.amplitude
            final_amp += amp
        self.assertAlmostEqual(final_amp, res.value)

    def test_observable_Z(self):
        nbqbits = 5

        term_coeff = -0.432
        term_op = "ZZZ"
        term_qbits = [2, 3, 4]
        obs = Observable(nbqbits)
        term = Term(term_coeff, term_op, term_qbits)
        obs.constant_coeff = 3.21
        obs.add_term(term)

        qfun = QRoutine()
        wires = qfun.new_wires(nbqbits)
        for i, qb in enumerate(wires):
            qfun.apply(RX(0.324 * i), qb)
        qfun.apply(Y.trans().ctrl(), wires[3], wires[2])
        qfun.apply(X.ctrl(2), wires[0], wires[1], wires[2])

        self._compare_expvalue_to_splitter_res(qfun, obs)

    def test_observable_paulis(self):
        nbqbits = 5

        term_coeff = -0.3
        term_op = "XYZ"
        term_qbits = [2, 3, 4]
        obs = Observable(nbqbits)
        term = Term(term_coeff, term_op, term_qbits)
        obs.constant_coeff = -0.2
        obs.add_term(term)

        qfun = QRoutine()
        wires = qfun.new_wires(nbqbits)
        for i, qb in enumerate(wires):
            qfun.apply(H, qb)
            qfun.apply(RZ(1.324 * (i + 1)), qb)
            qfun.apply(RY(0.724 * (i + 1)), qb)
        qfun.apply(Z.ctrl(), wires[1], wires[3])
        self._compare_expvalue_to_splitter_res(qfun, obs)

    def test_observable_tutorial(self):
        nbqbits = 5
        one_count = Observable(nbqbits)
        for i in range(nbqbits):
            one_count.add_term(Term(-0.5, "Z", [i]))
        one_count.constant_coeff += nbqbits / 2

        qfun = QRoutine()
        wires = qfun.new_wires(nbqbits)
        for i, qb in enumerate(wires):
            qfun.apply(RX(0.324 * i), qb)
        # qfun.apply(Z.ctrl(), wires[2], wires[3])
        qfun.apply(X, wires[0])
        qfun.apply(CNOT, wires[0], wires[2])
        self._compare_expvalue_to_splitter_res(qfun, one_count)
