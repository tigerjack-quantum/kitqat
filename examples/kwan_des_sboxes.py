from qat.lang.AQASM.gates import X, Z
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import RProgram
from qatext.qroutines.crypto.sbox.des.kwan import sboxes

# from qatext.utils.statistics.depth import compute_circuit_depth
from qatext.synthesis import cliffordt as ct

import numpy as np


def ex_s1():
    """Specific example with given input"""
    pr = Program()
    r_in = pr.qalloc(6)
    r_out = pr.qalloc(4)
    # x = qr.qalloc(63)

    # 011011
    for i in (1, 2, 4, 5):
        pr.apply(X, r_in[i])

    pr.apply(sboxes[4](), r_in, r_out)
    cr = pr.to_circ()
    print(cr.statistics())
    print(cr.nbqbits)
    rpr = RProgram.circuit_to_rprogram(cr)
    res = rpr.rbits.to01()
    # print(len(res))
    # if little_endian:
    #     res = res[::-1]
    print(res[6:10])


def ex_stats_sboxes():
    """All the S-boxes measures in terms of standard gates and Clifford+T gates"""
    linker = ct.get_new_cliffordt_linker()
    linker.add_signature(ct.x2)
    linker.add_signature(ct.y)
    linker.add_signature(ct.z)
    linker.add_signature(ct.qand1)

    boxes = {}
    for i, sbox in enumerate(sboxes):
        print("*" * 79)
        pr = Program()
        r_in = pr.qalloc(6)
        r_out = pr.qalloc(4)
        pr.apply(sbox(), r_in, r_out)
        cr = pr.to_circ()
        print("Statistics generic")
        stats = cr.statistics()
        print(stats)
        print("* depth - all *")
        depth_all = cr.depth(default=1)
        print(depth_all)
        print("* depth - CCNOT *")
        depth_ccnot = cr.depth(default=0, gate_times={"C-C-X": 1.0})
        print(depth_ccnot)
        print("Statistics Clifford+T")
        cr = pr.to_circ(inline=True)
        linker.link(cr)
        stats_t = cr.statistics()
        print(stats_t)
        # print("* depth - T *")
        # print(cr.depth(default=0, gate_times={"T": 1.0, "D-T": 1.0}))
        # cr.display()
        # input("A")
        nbqbits = stats["nbqbits"]
        row = f"S{i + 1} & "
        row += f"{nbqbits - 6} & "
        ccnot_gates = stats["gates"]["C-C-X"]
        row += f"{stats['gates']['X']} & {stats['gates']['CNOT']} & {ccnot_gates} & {depth_all} & "
        t_gates = stats_t["gates"]["T"] + stats_t["gates"]["D-T"]
        # qubits, clifford, t, depth
        # in the parallel implementation, we have as much ancillae as ccnot for each CCNOT decomposition
        # row += f"{ccnot_gates + nbqbits - 6} & {stats_t['gate_size'] - t_gates} & {t_gates} & {int(depth_ccnot)} \\\\"
        row += f"{ccnot_gates + nbqbits - 6}  & {t_gates} & {int(depth_ccnot)} \\\\"
        boxes[f"S{i + 1}"] = row
    print("-" * 79)
    print("-" * 79)
    for _, v in boxes.items():
        print(v)


def ex_sfirst_parallel():
    """Measures of a single round of compute, with all the S-boxes applied in
    parallel"""
    # To check the depth after 1 layer of 8 Sboxes application, w/out undo
    # Useful to get the no. of CCX and retrieve the overall results manually.
    #
    # print("*Only computation, no uncomputation, 1 round")
    pr = Program()

    r_in = pr.qalloc(48)
    r_out = pr.qalloc(32)

    #
    ancss = [
        pr.qalloc(63),
        pr.qalloc(56),
        pr.qalloc(57),
        pr.qalloc(42),
        pr.qalloc(62),
        pr.qalloc(57),
        pr.qalloc(57),
        pr.qalloc(54),
    ]

    for idx, sbox in enumerate(sboxes):
        pr.apply(
            sbox(),
            r_in[idx * 6 : idx * 6 + 6],
            r_out[idx * 4 : idx * 4 + 4],
            ancss[idx],
        )

    cr = pr.to_circ()
    stats_all = cr.statistics()
    depth_all = cr.depth(default=1)
    depth_ccnot = cr.depth(default=0, gate_times={"C-C-X": 1.0, "CCNOT": 1.0})

    meas = {}
    meas["W"] = cr.nbqbits
    meas["G"] = stats_all['gates']
    meas["D"] = depth_all
    meas["D-CCNOT"] = depth_ccnot
    return meas


def ex_retrieve(n_keys):
    """Overall measures of the Grover oracle, and the number of grover
    iterations, retrieved starting from the single compute measures of the previous function"""
    compute = ex_sfirst_parallel()

    pr = Program()
    keys = [None] * 3
    for i in range(n_keys):
        keys[i] = pr.qalloc(48)
        _ = pr.qalloc(8 * n_keys)
    for i in range(n_keys, 3):
        keys[i] = keys[0]
    # left
    _ = pr.qalloc(32)
    # right, already in meas
    # r_in = pr.qalloc(32)
    # r_out = pr.qalloc(32)

    uf_no = 1 if n_keys == 1 else 3

    overall = {}
    overall["W"] = compute["W"] * uf_no + pr.qbit_count
    overall["G"] = {k: v * 2 * 16 * 2 * uf_no for k, v in compute["G"].items()}
    overall["D"] = compute["D"] * 2 * 16 * 2 * uf_no + np.log2(64) + np.log2(n_keys * 56)

    overall2 = {}
    overall2["W"] = np.log2(overall["W"])
    overall2["G"] = {k: np.log2(v) for k, v in overall["G"].items() if v > 0}
    overall2["D"] = np.log2(overall["D"])
    overall2["iters"] = (n_keys * 55 /2) + np.log2(.58)

    cliffordt2 = {}
    width = overall["W"]
    width += compute['G']['C-C-X'] if uf_no == 1 else 0
    cliffordt2["W"] = np.log2(width)
    # Not times 4 since half of them is QAND and half is QAND^\dagger
    cliffordt2["T"] = overall2['G']["C-C-X"] * 2
    # same as before, uncompute stage doesn't count
    cliffordt2["D-T"] = np.log2(compute["D-CCNOT"] * 2 * 16 * uf_no + np.log2(64) + np.log2(n_keys * 56))
    cliffordt2["iters"] = (n_keys * 55 /2) + np.log2(.58)


    return overall, overall2, cliffordt2


def ex_sall():
    pr = Program()
    n_keys = 3  # 3DES2
    keys = [None] * 3
    for i in range(n_keys):
        keys[i] = pr.qalloc(48)
        _ = pr.qalloc(8 * n_keys)
    for i in range(n_keys, 3):
        keys[i] = keys[0]
    # left
    l_in = pr.qalloc(32)
    # right
    r_in = pr.qalloc(32)
    # right out
    r_out = pr.qalloc(32)

    # 3 bcz its enc(dec(enc)) * 2 for uncompute
    for i in range(3):
        # 16 rounds
        for _ in range(16):
            for idx, sbox in enumerate(sboxes):
                pr.apply(
                    sbox(), r_in[idx * 6 : idx * 6 + 6], r_out[idx * 4 : idx * 4 + 4]
                )

            # This does not require qubits, the other ancillae of the S-boxes are clean
            # pr.apply(Z.ctrl(len(key) - 1), key)

            for idx, sbox in enumerate(sboxes):
                pr.apply(
                    sbox().dag(),
                    r_in[idx * 6 : idx * 6 + 6],
                    r_out[idx * 4 : idx * 4 + 4],
                )

    cr = pr.to_circ()
    print("*" * 79)
    print("Only S-boxes")
    stats = cr.statistics()
    print(stats)
    # print("* nbqbits *")
    # print(cr.nbqbits)
    # print("* depth 1 *")
    # print(compute_circuit_depth(cr))
    print("* depth - w/out multi-controlled *")
    print(cr.depth(default=1))

    print("*" * 79)
    print("Multi-controlled decomposition of oracle and diffusion")
    # For the oracle, Note that there's a C^nZ gate w/ 64 qubits. For its
    # decomposition, we can reuse the ancillary qubits of the S-boxes; the
    # depth is increased of log(64)=6; the C-C-X count is increased by 2*64-1 =
    # 127, while the C-Z count by 1. Instead of C-Z, we can keep 1 CNOT + 2 H.
    stats["gates"]["C-C-X"] += 127

    # For the diffusion, the C^nZ gate has 56 * n_keys

    print("* depth 2 - CCNOT *")
    print(cr.depth(default=0, gate_times={"C-C-X": 1.0}))


def main():
    # ex_s1()
    # ex_stats_sboxes()
    uf_measures = ex_sfirst_parallel()
    print(uf_measures)
    print("*" * 79)

    for n_keys in range(1, 4):
        overall, overall2, cliffordt2 = ex_retrieve(n_keys)
        print(overall)
        print(overall2)
        print(cliffordt2)
        print("-" * 79)

    # ex_sall()


if __name__ == "__main__":
    main()
