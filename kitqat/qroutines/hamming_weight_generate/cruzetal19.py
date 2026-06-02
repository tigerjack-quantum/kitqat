"""Based on
Diogo Cruz, Romain Fournier, Fabien Gremion, Alix Jeannerot, Kenichi
Komagata, Tara Tosic, Jarla Thiesbrummel, Chun Lam Chan, Nicolas
Macris, Marc-Andr´e Dupertuis, and Cl´ement Javerzac-Galy. Efficient
Quantum Algorithms for GHZ and W States, and Implementation on
the IBM Quantum Computer. Advanced Quantum Technologies, 2(5-
6):1900015, 2019.
"""
import numpy as np
from qat.lang.AQASM.gates import CNOT, RY, X
from qat.lang.AQASM.misc import build_gate
from qat.lang.AQASM.routines import QRoutine


def build_dichotomy_tree(n):
    """
    Build the dichotomy tree for W_n as described in the paper.
    Returns a list of levels, each level being a list of (n1, n2, qubit_index) tuples,
    where qubit_index is the control qubit for the block B(n1/n2).

    We represent the tree as a list of (n1, n2, ctrl_qubit, tgt_qubit) operations
    in circuit order (level by level).
    """
    # Each tree node: (n1, n2, ctrl_wire, tgt_wire)
    # The root acts on wire 0 (ctrl) and wire floor(n/2) (tgt)
    ops_by_level = []

    # Queue entries: (n1, n2, ctrl_wire, tgt_wire)
    # Root: dichotomy of n: lower=floor(n/2), upper=ceil(n/2)
    # qubit allocation: ctrl_wire gets the "upper" half, tgt_wire gets the "lower" half
    # Wire assignments: the subtree rooted at ctrl covers ceil(n/2) qubits starting at ctrl_wire
    #                   the subtree rooted at tgt  covers floor(n/2) qubits starting at tgt_wire

    def build(n1, n2, ctrl_wire, tgt_wire, level):
        """
        Node (n1, n2) corresponds to block B(n1/n2).
        ctrl_wire: wire that was the control of this block (the "upper line" of parent)
        tgt_wire:  wire that is the new target (the "lower line" of parent after CNOT)
        """
        if len(ops_by_level) <= level:
            ops_by_level.append([])
        ops_by_level[level].append((n1, n2, ctrl_wire, tgt_wire))
        if n2 <= 1:
            return
        # Upper child: dichotomy of n1 (upper part)
        n1_upper = (n1 + 1) // 2   # ceil(n1/2)
        # n1_lower = n1 // 2          # floor(n1/2)
        # Lower child: dichotomy of (n2 - n1)
        n2_rest = n2 - n1
        n2_upper = (n2_rest + 1) // 2
        # n2_lower = n2_rest // 2
        # The upper child's ctrl is ctrl_wire, its tgt is ctrl_wire + ceil(n1/2)
        # The lower child's ctrl is tgt_wire,  its tgt is tgt_wire  + ceil((n2-n1)/2)
        if n1 >= 2:
            build(n1_upper, n1, ctrl_wire, ctrl_wire + n1_upper, level + 1)
        if n2 - n1 >= 2:
            build(n2_upper, n2_rest, tgt_wire, tgt_wire + n2_upper, level + 1)
    # lower = n // 2
    upper = (n + 1) // 2
    build(upper, n, 0, upper, 0)
    return ops_by_level


def apply_B(routine, wires, p, ctrl, tgt):
    """
    Apply block B(p): controlled-G(p) on (ctrl -> tgt), then CNOT(tgt -> ctrl).

    Controlled-G(p) decomposition (4-gate form from paper):
      CG(p) = [I ⊗ RY(θ/2)] CNOT [I ⊗ RY(-θ/2)] CNOT
    where cos(θ/2) = sqrt(p), i.e. θ = 2*arccos(sqrt(p)).
    First qubit is control, second is target.

    Then inverted CNOT: CNOT with ctrl=tgt, target=ctrl.
    """
    theta = 2 * np.arccos(np.sqrt(p))

    # Controlled-G(p): control=ctrl, target=tgt
    routine.apply(RY(theta / 2),  wires[tgt])
    routine.apply(CNOT,           wires[ctrl], wires[tgt])
    routine.apply(RY(-theta / 2), wires[tgt])
    routine.apply(CNOT,           wires[ctrl], wires[tgt])

    # Inverted CNOT (ctrl and tgt swapped)
    routine.apply(CNOT, wires[tgt], wires[ctrl])

@build_gate("W_STATE", [int], arity=lambda x: x)
def w_state(n: int):
    qr = QRoutine()
    qbits = qr.new_wires(n)

    # Initialize: set qubit 0 to |1>
    if n == 1:
        return qr
    qr.apply(X, qbits[0])

    # Get the dichotomy tree
    ops_by_level = build_dichotomy_tree(n)

    # Apply each level
    for level_ops in ops_by_level:
        for (n1, n2, ctrl, tgt) in level_ops:
            if n1 == 0 or n2 == 0:
                continue
            p = n1 / n2
            apply_B(qr, qbits, p, ctrl, tgt)
    return qr
