from qat.lang.AQASM.gates import CNOT, AbstractGate, RY, Z, ParamGate
from qat.lang.AQASM.routines import QRoutine

MRY = AbstractGate("RY", [], arity=1, circuit_generator=lambda theta: CustomRY(theta))
# MCRY = AbstractGate("C-RY", [float], arity=2, circuit_generator=lambda theta: mcry_simple(theta))
# MCCRY = AbstractGate("C-C-RY", [float], arity=3, circuit_generator=lambda theta: mcry_simple(theta))


class CustomRY(ParamGate):
    def __init__(self, theta):
        super(CustomRY, self).__init__(MRY, [theta])
        self.angle = theta

    def ctrl(self, nbcontrols=1):
        qfun = QRoutine()
        ctrl = qfun.new_wires(nbcontrols)
        tgt = qfun.new_wires(1)
        ### HERE GOES YOUR CUSTOM C-RY implementation
        if nbcontrols == 1:
            qfun.apply(CNOT, ctrl, tgt)
            qfun.apply(RY(-self.angle / 2), tgt)
            qfun.apply(CNOT, ctrl, tgt)
            qfun.apply(RY(self.angle / 2), tgt)
        elif nbcontrols == 2:
            qfun.apply(CNOT, ctrl[1], tgt)
            qfun.apply(RY(-self.angle / 4), tgt)
            qfun.apply(CNOT, ctrl[0], tgt)
            qfun.apply(RY(self.angle / 4), tgt)
            qfun.apply(CNOT, ctrl[1], tgt)
            qfun.apply(RY(-self.angle / 4), tgt)
            qfun.apply(CNOT, ctrl[0], tgt)
            qfun.apply(RY(self.angle / 4), tgt)
        else:
            raise Exception("Not implemented for ctrls > 2")
        return qfun
