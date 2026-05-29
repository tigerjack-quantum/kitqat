from qat.lang.AQASM.gates import X
from qat.lang.AQASM.routines import QRoutine
from qatext.qatmgmt.routines import QRoutineWrapper
from qatext.qroutines.datastructure.array import contains
from qatext.qroutines.datastructure.sliding_sort_array import \
    delete, insert
# as insert_ld, insert_lw  # ld stands for low-depth
# from qatext.qroutines.datastructure.sliding_sort_array import insert_lw
from qatext.qroutines.qregs_mgmt import qregs_init as qi
# from qatext.qroutines.qregs_mgmt import qregs_init_bix as bix

def update_reversible(n, k, m, wstate_ones, wstate_zeros):
    # TODO temp
    has_duplicates = False
    qrw = QRoutineWrapper(QRoutine())
    qrw._qroutine.name = "update"

    node_s_ones = qrw.qarray_wires(k, m, "s_1", int)
    node_s_zeros = qrw.qarray_wires(n - k, m, "s_0", int)
    node_t_ones = qrw.qarray_wires(k, m, "t_1", int)
    node_t_zeros = qrw.qarray_wires(n - k, m, "t_0", int)
    # since we are bounded by # of qubits, this is unrolled classically

    wstate_ones = qrw.qarray_wires(k, 1, "w_1", str)
    wstate_zeros = qrw.qarray_wires(n - k, 1, "w_0", str)
    alpha_ones = qrw.qarray_wires(1, m, "a_1", int)
    alpha_zeros = qrw.qarray_wires(1, m, "a_0", int)
    qbit_out = qrw.qarray_wires(1, 1, "out", bool)
    # TODO temp, should be ancilla, now kept normal just for debugging

    # qrw.set_ancillae(alpha_ones)
    # qrw.set_ancillae(alpha_zeros)
    # qrw.set_ancillae(qbit_out)

    # copy s to t
    qrw.apply(qi.copy_array_of_registers(k, m), node_s_ones, node_t_ones)
    qrw.apply(qi.copy_array_of_registers(n - k, m), node_s_zeros, node_t_zeros)
    # return qrw._qroutine

    # qrw.apply(generate(k, 1), wstate_ones)
    # qrw.apply(generate(n - k, 1), wstate_zeros)

    qrout_copy_cell = qi.copy_register(m)
    for j in range(k):
        qrw.apply(qrout_copy_cell.ctrl(), wstate_ones[j],
                    node_s_ones[j], alpha_ones)

    for j in range(n - k):
        qrw.apply(qrout_copy_cell.ctrl(), wstate_zeros[j],
                node_s_zeros[j], alpha_zeros)
    # return qrw._qroutine

    qrout_insert_ones = insert(k, m)
    qrout_insert_zeros = insert(n - k, m)
    qrout_delete_ones = delete(k, m)
    qrout_delete_zeros = delete(n - k, m)
    # delete the selected elements (in alpha_ones) from node_t_ones
    qrw.apply(qrout_delete_ones, alpha_ones, node_t_ones)
    # delete the selected elements (in alpha_zeros) from node_t_zeros
    qrw.apply(qrout_delete_zeros, alpha_zeros, node_t_zeros)
    # return qrw._qroutine
    # insert in node_s_ones the value stored in alpha_zeros, and viceversa
    qrw.apply(qrout_insert_ones, alpha_zeros, node_t_ones)
    qrw.apply(qrout_insert_zeros, alpha_ones, node_t_zeros)
    # return qrw._qroutine

    qrout_contains_ones = contains(k, m, has_duplicates)
    qrout_contains_zeros = contains(n - k, m, has_duplicates)

    # RESET w states
    for j in range(k):
        # check if node_s_ones[j] is present in node_t_ones and, if not,
        # apply X to w[j]
        qrw.apply(qrout_contains_ones, node_s_ones[j], node_t_ones,
                    qbit_out)
        qrw.apply(X, qbit_out)
        qrw.apply(X.ctrl(), qbit_out, wstate_ones[j])
        qrw.apply(qrout_copy_cell.ctrl(), qbit_out, node_s_ones[j], alpha_ones)
        qrw.apply(X, qbit_out)
        qrw.apply(qrout_contains_ones, node_s_ones[j], node_t_ones,
                    qbit_out)
    # return qrw._qroutine

    qrw.apply(X, qbit_out)
    for j in range(n - k):
        # check if node_s_ones[j] is present in node_t_ones and, if not, apply
        # X to w[j]
        qrw.apply(qrout_contains_zeros, node_s_zeros[j], node_t_zeros,
                    qbit_out)
        qrw.apply(X.ctrl(), qbit_out, wstate_zeros[j])
        qrw.apply(qrout_copy_cell.ctrl(), qbit_out, node_s_zeros[j], alpha_zeros)
        qrw.apply(qrout_contains_zeros, node_s_zeros[j], node_t_zeros,
                    qbit_out)
    qrw.apply(X, qbit_out)

    return qrw._qroutine
