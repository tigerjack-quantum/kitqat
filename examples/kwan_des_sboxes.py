import numpy as np
from qat.lang.AQASM.gates import X
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import RProgram
from qatext.qroutines.crypto.sbox.des.kwan import sboxes

# from qatext.utils.statistics.depth import compute_circuit_depth
from qatext.synthesis import cliffordt as ct


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
    """Measures of a single round of compute for a single U_E, with all the
    S-boxes applied in parallel.
    """
    # To check the depth after 1 layer of 8 Sboxes application, w/out undo
    # Useful to get the no. of CCX and retrieve the overall results manually.
    #
    # print("*Only computation, no uncomputation, 1 round")
    pr = Program()

    r_in = pr.qalloc(48)
    r_out = pr.qalloc(32)

    # the ancillary qubits
    ancss = [
        pr.qalloc(59),
        pr.qalloc(52),
        pr.qalloc(53),
        pr.qalloc(38),
        pr.qalloc(58),
        pr.qalloc(53),
        pr.qalloc(53),
        pr.qalloc(50),
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
    meas["G"] = stats_all["gates"]
    meas["D"] = depth_all
    meas["D-CCNOT"] = depth_ccnot
    return meas


def ex_retrieve(n_keys):
    """Overall measures of the Grover oracle, retrieved starting from the
    single compute measures of the previous function, and the number of grover
    iterations

    """
    compute = ex_sfirst_parallel()

    # number of times we have to execute the U_f unitary. It's 1 for DES and 3
    # for 3DES(-2 or -3)
    uf_no = 1 if n_keys == 1 else 3

    overall = {}
    # Not multiplied by uf_no since the U_F and U_F^\dagger of each U_E will
    # leave, in the end, the ancillary qubits clean, and they can be reused. We
    # just have to add to the qubits count the keys and the left part of the
    # plaintext.
    width = compute["W"] + n_keys * 56 + 32
    # * 2 bcz U_F and U_F^\dagger of each round.
    # * 16 bcz of no. of rounds of each U_E.
    # * 2 bcz of compute/uncompute (that is, U_f and U_f^\dagger) of oracle.
    # * uf_no bcz this has to be done for every U_f unitary.
    overall["G"] = {k: v * 2 * 16 * 2 * uf_no for k, v in compute["G"].items() if v > 0}
    # init + 2 to implement the CZ of the oracle + diffusion
    overall["G"]["H"] = n_keys + 2 + n_keys * 2
    # The X required at each diffusion
    overall["G"]["X"] = overall["G"]["X"] + n_keys * 2

    # The CNOT required by EP, Key mix, and the L-S xor F(R)
    overall["G"]["CNOT"] = overall["G"]["CNOT"] + (16 + 48 + 32) * 2 * 16 * 2 * uf_no
    # the log factors are for the reflection decompositions
    overall["D"] = (
        compute["D"] * 2 * 16 * 2 * uf_no + 2 * np.log2(64) + 2 * np.log2(n_keys * 56)
    )
    # The decomposition of the CCX for the 2 reflections will use:
    # for DES: 1) oracle, 62 bits; 2) diffusion: 56 qubits
    # for 3DES: 1) oracle, 62 bits; 2) diffusion: 56*2 or 56*3 qubits
    #
    # In all cases, we can reuse the ancillary qubits of the S-boxes, and we
    # don't need any additional one.
    width += 0
    overall["W"] = width

    overall2 = {}
    overall2["W"] = np.log2(overall["W"])
    overall2["G"] = {k: np.log2(v) for k, v in overall["G"].items()}
    overall2["D"] = np.log2(overall["D"])
    # 55 instead of 56 bcz of complimentary property of DES and 3DES
    # logarithmic factor is the optimal no. of iterations
    overall2["iters"] = (n_keys * 55 / 2) + np.log2(0.58)

    cliffordt2 = {}
    # for each CCX of the S-boxes, we add 1 bit to have a T-depth 1
    # decomposition.
    width = overall["W"] + compute["G"]["C-C-X"]
    cliffordt2["W"] = np.log2(width)
    # Divided by 2 since half of them is QAND and half is QAND^\dagger
    cliffordt2["T"] = overall2["G"]["C-C-X"] - 1
    # same as before, uncompute stage doesn't count
    cliffordt2["D-T"] = np.log2(
        compute["D-CCNOT"] * 2 * 16 * uf_no + 2 * np.log2(64) + 2 * np.log2(n_keys * 56)
    )
    cliffordt2["iters"] = overall2["iters"]

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
    _ = pr.qalloc(32)
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

    header = f"Variant & W & X & CX & CCX & D & D$\\times$W & W & T & T-D & T-D$\\times$W\\\\"
    print(header)
    for n_keys in range(1, 4):
        _, overall2, cliffordt2 = ex_retrieve(n_keys)
        # print(overall)
        # print(overall2)
        # print(cliffordt2)
        # qubits
        if n_keys == 1:
            head = "DES"
        elif n_keys == 2:
            head = "3DES2"
        elif n_keys == 3:
            head = "3DES3"
        iters = overall2["iters"]
        row = f"{head} &"
        row += f"{round(overall2['W'])} & "
        row += f"{round(overall2['G']['X'] + iters)} & "
        row += f"{round(overall2['G']['CNOT'] + iters)} & "
        row += f"{round(overall2['G']['C-C-X'] + iters)} & "
        row += f"{round(overall2['D'] + iters)} & "
        row += f"{round(overall2['D'] + iters + overall2['W'])} & "

        row += f"{round(cliffordt2['W'])} & "
        row += f"{round(cliffordt2['T'] + iters)} & "
        row += f"{round(cliffordt2['D-T'] + iters)} & "
        row += f"{round(cliffordt2['D-T'] + iters + overall2['W'])}\\\\"
        print(row)

    # ex_sall()


if __name__ == "__main__":
    main()
