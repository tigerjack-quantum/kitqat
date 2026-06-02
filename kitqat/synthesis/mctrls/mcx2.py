"""My multi-controlled X gate decomposition in terms of logarithmic-depths Toffoli."""
from qat.lang.AQASM import QRoutine, CNOT, CCNOT, X, AbstractGate
from qat.lang.AQASM.misc import build_gate
import numpy as np

abstract = AbstractGate("NOT", [], arity=1)


class XMulti(QRoutine):
    def __init__(self):
        super().__init__()
        wr = self.new_wires(1)
        self.apply(abstract(), wr)

    def ctrl(self, nbctrls=1):
        qr = QRoutine()
        wr = qr.new_wires(nbctrls)
        wt = qr.new_wires(self.arity)
        match nbctrls:
            case 0:
                return self
            case 1:
                qr.apply(CNOT, 0, 1)
            case 2:
                qr.apply(CCNOT, 0, 1, 2)
            case _:
                # Assume power of 2 for now
                anc = qr.new_wires(nbctrls - 2)

                layers_compute = int(np.ceil(np.log2(nbctrls)))
                # print(f"layers c = {layers_compute}")
                # layers += 2 # I think only if more than 8
                ctrl_qubits = list(zip(*(iter(wr),) * 2))
                anc_used = 0

                for layer in range(layers_compute - 1):
                    # print(f"layer {layer}")
                    # print(f"ctlrs {ctrl_qubits}")
                    tgt_qubits = [anc[i + anc_used] for i in range(len(ctrl_qubits))]
                    # print(f"tgt {tgt_qubits}")
                    anc_used += len(tgt_qubits)
                    for ctrls, tgt in zip(ctrl_qubits, tgt_qubits):
                        qr.apply(CCNOT, ctrls[0], ctrls[1], tgt)

                    ctrl_qubits = list(zip(*(iter(tgt_qubits),) * 2))
                # print(f"ctlrs {ctrl_qubits}")

                qr.apply(CCNOT, ctrl_qubits[0][0], ctrl_qubits[0][1], wt)

                ctrl_qubits = list(zip(*(iter(wr),) * 2))
                anc_used = 0
                for layer in range(layers_compute - 1):
                    # print(f"layer {layer}")
                    # print(f"ctlrs {ctrl_qubits}")
                    tgt_qubits = [anc[i + anc_used] for i in range(len(ctrl_qubits))]
                    # print(f"tgt {tgt_qubits}")
                    anc_used += len(tgt_qubits)
                    for ctrls, tgt in zip(ctrl_qubits, tgt_qubits):
                        qr.apply(CCNOT, ctrls[0], ctrls[1], tgt)
                    # ctrls_pairs = nbctrls // (2**(layer+1))
                    # ctrl_qubits = list(zip(*(,)) * 2)
                    ctrl_qubits = list(zip(*(iter(tgt_qubits),) * 2))

        return qr

@build_gate("X", [], arity=1)
def x():
    return XMulti()

@build_gate("NOT", [], arity=1)
def mnot():
    return X()
