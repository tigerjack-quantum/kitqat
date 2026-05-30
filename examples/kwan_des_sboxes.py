import numpy as np
from qat.lang.AQASM.gates import X
from qat.lang.AQASM.program import Program
from qatext.qpus.reversible import RProgram, RSimulator
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
    rpr = RSimulator.from_circuit(cr)
    res = rpr.rbits.to01()
    # print(len(res))
    # if little_endian:
    #     res = res[::-1]
    print(res[6:10])


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


def get_sboxes_measures():
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


def get_sboxes_parallel_measures():
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


def get_sboxes_sequential_measures():
    """Measures of a single round of compute for a single U_E, with all the
    S-boxes applied sequentially. That is, S1 (out on 4 qubits, xor of those to
    Left), undo S1, S2 (...) undo S2, ...

    """
    # To check the depth after 1 layer of 8 Sboxes application, w/out undo
    # Useful to get the no. of CCX and retrieve the overall results manually.
    #
    # print("*Only computation, no uncomputation, 1 round")
    pr = Program()

    r_in = pr.qalloc(48)
    # only 4, because we undo each time
    r_out = pr.qalloc(4)

    # the ancillary qubits
    ancs = pr.qalloc(59)

    for idx, sbox in enumerate(sboxes):
        pr.apply(
            sbox(),
            r_in[idx * 6 : idx * 6 + 6],
            r_out[idx * 4 : idx * 4 + 4],
            ancs,
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


def get_encryption_measures_parallel(n_keys):
    compute = get_sboxes_parallel_measures()

    # number of times we have to execute the U_f unitary. It's 1 for DES and 3
    # for 3DES(-2 or -3)
    uf_no = 1 if n_keys == 1 else 3

    overall = {}
    # Not multiplied by uf_no since the U_F and U_F^\dagger of each U_E will
    # leave, in the end, the ancillary qubits clean, and they can be reused. We
    # just have to add to the qubits count the keys and the left part of the
    # plaintext.
    overall["W"] = compute["W"] + n_keys * 56 + 32
    # * 2 bcz U_F and U_F^\dagger of each round.
    # * 16 bcz of no. of rounds of each U_E.
    # * uf_no bcz this has to be done for every U_E unitary.
    overall["G"] = {k: v * 2 * 16 * uf_no for k, v in compute["G"].items() if v > 0}

    # The CNOT required by EP, Key mix, and the L-S xor F(R)
    overall["G"]["CNOT"] = overall["G"]["CNOT"] + (16 + 48 + 32) * 2 * 16 * uf_no
    overall["D"] = compute["D"] * 2 * 16 * uf_no
    overall["D-CCNOT"] = compute["D-CCNOT"] * 2 * 16 * uf_no

    overall2 = {}
    overall2["W"] = np.log2(overall["W"])
    overall2["G"] = {k: np.log2(v) for k, v in overall["G"].items()}
    overall2["D"] = np.log2(overall["D"])
    overall2["D-CCNOT"] = np.log2(overall["D-CCNOT"])

    cliffordt = {}
    # for each CCX of the S-boxes, we add 1 qubit to have a T-depth 1, T-count
    # 4 decomposition. It also requires 10 Clifford for QAND, and 3 Clifford +
    # 2 classically controlled Clifford for QAND^\dagger. We can just add, for
    # the classically controlled, half of them (i.e., 1), since the classical
    # qubit is on half of the time.
    cliffordt["W"] = overall["W"] + compute["G"]["C-C-X"]
    # non T gates, i.e., Clifford
    cliffordt["nT"] = (
        overall["G"]["X"]
        + overall["G"]["CNOT"]
        + (overall["G"]["C-C-X"] / 2 * 10 + overall["G"]["C-C-X"] / 2 * 4)
    )
    # Divided by 2 since half of them is QAND and half is QAND^\dagger
    cliffordt["T"] = overall["G"]["C-C-X"] * 4 / 2
    cliffordt["D-T"] = compute["D-CCNOT"] * 2 * 16 * uf_no

    cliffordt2 = {}
    # for each CCX of the S-boxes, we add 1 bit to have a T-depth 1
    # decomposition.
    cliffordt2["W"] = np.log2(cliffordt["W"])
    # Divided by 2 since half of them is QAND and half is QAND^\dagger
    cliffordt2["T"] = overall2["G"]["C-C-X"] - 1
    # non T gates, i.e., Clifford
    cliffordt2["nT"] = np.log2(cliffordt["nT"])
    # same as before, uncompute stage doesn't count
    cliffordt2["D-T"] = np.log2(compute["D-CCNOT"] * 2 * 16 * uf_no)

    return overall, overall2, cliffordt, cliffordt2


def get_encryption_measures_sequential(n_keys):
    compute = get_sboxes_sequential_measures()

    # number of times we have to execute the U_f unitary. It's 1 for DES and 3
    # for 3DES(-2 or -3)
    uf_no = 1 if n_keys == 1 else 3

    overall = {}
    # Not multiplied by uf_no since the U_F and U_F^\dagger of each U_E will
    # leave, in the end, the ancillary qubits clean, and they can be reused. We
    # just have to add to the qubits count the keys and the left part of the
    # plaintext.
    overall["W"] = compute["W"] + n_keys * 56 + 32
    # * 2 bcz U_F and U_F^\dagger of each round.
    # * 16 bcz of no. of rounds of each U_E.
    # * uf_no bcz this has to be done for every U_E unitary.
    overall["G"] = {k: v * 2 * 16 * uf_no for k, v in compute["G"].items() if v > 0}
    overall["G-sum"] = sum(overall["G"].values())
    # The CNOT required by EP, Key mix, and the L-S xor F(R)
    overall["G"]["CNOT"] = overall["G"]["CNOT"] + (16 + 48 + 32) * 2 * 16 * uf_no
    overall["D"] = compute["D"] * 2 * 16 * uf_no
    overall["D-CCNOT"] = compute["D-CCNOT"] * 2 * 16 * uf_no

    overall2 = {}
    overall2["W"] = np.log2(overall["W"])
    overall2["G"] = {k: np.log2(v) for k, v in overall["G"].items()}
    # input(overall['G-sum'])
    overall2["G-sum"] = np.log2(overall["G-sum"])
    overall2["D"] = np.log2(overall["D"])
    overall2["D-CCNOT"] = np.log2(overall["D-CCNOT"])

    cliffordt = {}
    # Decomposition based on a T-depth 2, T-count 4, no ancilla. See Meuli et
    # al. 2022, citing others. The QAND requires 10 Cliffords; the QAND^\dagger
    # is identical to the previous.
    cliffordt["W"] = overall["W"]
    # non T gates, i.e., Clifford
    cliffordt["nT"] = (
        overall["G"]["X"]
        + overall["G"]["CNOT"]
        + (overall["G"]["C-C-X"] / 2 * 10 + overall["G"]["C-C-X"] / 2 * 4)
    )
    # Divided by 2 since half of them is QAND and half is QAND^\dagger
    cliffordt["T"] = overall["G"]["C-C-X"] * 4 / 2
    cliffordt["D-T"] = compute["D-CCNOT"] * 2 * 2 * 16 * uf_no

    cliffordt2 = {}
    # for each CCX of the S-boxes, we add 1 bit to have a T-depth 1
    # decomposition.
    cliffordt2["W"] = np.log2(cliffordt["W"])
    cliffordt2["nT"] = np.log2(cliffordt["nT"])
    # Divided by 2 since half of them is QAND and half is QAND^\dagger
    cliffordt2["T"] = overall2["G"]["C-C-X"] - 1
    # same as before, uncompute stage doesn't count
    cliffordt2["D-T"] = np.log2(compute["D-CCNOT"] * 2 * 16 * uf_no)

    return overall, overall2, cliffordt, cliffordt2


def get_iters(n_keys):
    return (n_keys * 55 / 2) + np.log2(0.58)


def get_oracle_parallel_measures(n_keys):
    """Overall measures of the Grover oracle, retrieved starting from the
    single compute measures of the previous function, and the number of grover
    iterations

    """
    overall, overall2, cliffordt, cliffordt2 = get_encryption_measures_parallel(n_keys)
    # 55 instead of 56 bcz of complimentary property of DES and 3DES; the
    # logarithmic factor is due to the optimal no. of iterations
    iters = get_iters(n_keys)

    # init + 2 to implement the CZ of the oracle + diffusion
    overall["G"]["H"] = n_keys + 2 + n_keys * 2
    # The X required to XOR the given ctx, estimated to be half of the ctx length
    overall["G"]["X"] = overall["G"]["X"] + 32 * 2
    # The decomposition of the CCX for the 2 reflections will use:
    # for DES: 1) oracle, 62 bits; 2) diffusion: 56 qubits
    # for 3DES: 1) oracle, 62 bits; 2) diffusion: 56*2 or 56*3 qubits
    #
    # In all cases, we can reuse the ancillary qubits of the S-boxes, and we
    # don't need any additional one.
    n_ccnot_phaseflip_decomposition = (64 - 1) * 2
    overall["G"]["C-C-X"] = overall["G"]["C-C-X"] + n_ccnot_phaseflip_decomposition
    overall["G-sum"] = sum(overall["G"].values())

    # the log factors are for the reflection decompositions
    overall["D"] = overall["D"] + np.log2(64)
    overall["D-CCNOT"] = overall["D-CCNOT"] + np.log2(64)

    overall2 = {}
    overall2["W"] = np.log2(overall["W"])
    overall2["G"] = {k: np.log2(v) + iters + 1 for k, v in overall["G"].items()}
    overall2["G-sum"] = np.log2(overall["G-sum"]) + iters + 1
    overall2["D"] = np.log2(overall["D"]) + iters + 1
    overall2["D-CCNOT"] = np.log2(overall["D"]) + iters + 1

    # Each CCX of the phase flip requires 10 Clifford for QAND, and 3 Clifford
    # + 2 classically controlled Clifford for QAND^\dagger. We can just add,
    # for the classically controlled, half of them (i.e., 1), since the
    # classical qubit is on half of the time. We do not need any additional
    # qubit for the oracle phase flip, since we can reuse the ones used for
    # S-boxes (both ancillary and QAND related).

    # non T gates, i.e., Clifford
    cliffordt["nT"] += n_ccnot_phaseflip_decomposition / 2 * 14
    # Divided by 2 since half of them is QAND and half is QAND^\dagger. The
    # QAND requires 4 T gates.
    cliffordt["T"] += n_ccnot_phaseflip_decomposition * 4 / 2
    cliffordt["D-T"] += np.log2(64)

    cliffordt2 = {}
    # for each CCX of the S-boxes, we add 1 bit to have a T-depth 1
    # decomposition.
    cliffordt2["W"] = np.log2(cliffordt["W"])
    # Divided by 2 since half of them is QAND and half is QAND^\dagger
    cliffordt2["nT"] = np.log2(cliffordt["nT"]) + iters + 1
    cliffordt2["T"] = np.log2(cliffordt["T"]) + iters + 1
    # same as before, uncompute stage doesn't count
    cliffordt2["D-T"] = np.log2(cliffordt["D-T"]) + iters + 1

    return overall, overall2, cliffordt, cliffordt2


def get_oracle_sequential_measures(n_keys):
    """Overall measures of the Grover oracle, retrieved starting from the
    single compute measures of the previous function, and the number of grover
    iterations."""
    overall, overall2, cliffordt, cliffordt2 = get_encryption_measures_sequential(
        n_keys
    )
    # 55 instead of 56 bcz of complimentary property of DES and 3DES; the
    # logarithmic factor is due to the optimal no. of iterations
    iters = (n_keys * 55 / 2) + np.log2(0.58)

    # init + 2 to implement the CZ of the oracle + diffusion
    overall["G"]["H"] = n_keys + 2 + n_keys * 2
    # The X required to XOR the given ctx, estimated to be half of the ctx length
    overall["G"]["X"] = overall["G"]["X"] + 32 * 2

    # The decomposition of the CCX for the oracle reflection uses 63 bits. For
    # the sequential case, we can reuse (some of) the ancillary qubits of the
    # S5 box (that is, 59 of them), and need just 3 additional ones.

    n_ccnot_phaseflip_decomposition = (64 - 1) * 2
    overall["W"] += 4
    overall["G"]["C-C-X"] = overall["G"]["C-C-X"] + n_ccnot_phaseflip_decomposition
    overall["G-sum"] = sum(overall["G"].values())

    # the log factors are for the reflection decompositions
    overall["D"] = overall["D"] + np.log2(64)
    overall["D-CCNOT"] = overall["D-CCNOT"] + np.log2(64)

    overall2 = {}
    overall2["W"] = np.log2(overall["W"])
    overall2["G"] = {k: np.log2(v) + iters + 1 for k, v in overall["G"].items()}
    overall2["G-sum"] = np.log2(overall["G-sum"]) + iters + 1
    overall2["D"] = np.log2(overall["D"]) + iters + 1
    overall2["D-CCNOT"] = np.log2(overall["D"]) + iters + 1

    # Each CCX of the phase flip requires 10 Clifford for QAND, and 3 Clifford
    # + 2 classically controlled Clifford for QAND^\dagger. We can just add,
    # for the classically controlled, half of them (i.e., 1), since the
    # classical qubit is on half of the time.
    #
    # For the decomposition of the CCX into QAND and QAND^\dagger, we need 63
    # QAND and the same number of dagger for the decomposition of the 64-block
    # multi-controlled phase flips. Each QAND requires one additional qubit.
    cliffordt["W"] = overall["W"] + 63
    # non T gates, i.e., Clifford
    cliffordt["nT"] += n_ccnot_phaseflip_decomposition / 2 * 14
    # Divided by 2 since half of them is QAND and half is QAND^\dagger. The
    # QAND requires 4 T gates.
    cliffordt["T"] += n_ccnot_phaseflip_decomposition * 4 / 2
    cliffordt["D-T"] += np.log2(64)

    cliffordt2 = {}
    # for each CCX of the S-boxes, we add 1 bit to have a T-depth 1
    # decomposition.
    cliffordt2["W"] = np.log2(cliffordt["W"])
    # Divided by 2 since half of them is QAND and half is QAND^\dagger
    cliffordt2["nT"] = np.log2(cliffordt["nT"]) + iters + 1
    cliffordt2["T"] = np.log2(cliffordt["T"]) + iters + 1
    # same as before, uncompute stage doesn't count
    cliffordt2["D-T"] = np.log2(cliffordt["D-T"]) + iters + 1

    return overall, overall2, cliffordt, cliffordt2


def print_comparison_ciphers_encryption_measures():
    # Jaques
    row = "AES-128~\\cite{jaques2019implementing}"
    row = "AES-128~\\cite{jaques2019implementing}"
    # Table 9 10
    row = "Camellia-128~\\cite{lin2023FurtherInsightsConstructing}"
    row += "& 388 & 3566 & 39600 & 10816 & - & 5284 & 2050192 & 388 & 140510 & 68320 & 22188 & 6150576 \\\\ "
    print(row)
    # Table 11
    row = "Camellia-128~\\cite{lin2023FurtherInsightsConstructing}"
    row += "& - & - & - & - & - & - & - & 992 & 180206 & 24960 & 92 & 91264 \\\\ "
    print(row)
    row = "SEED\\cite{oh2023OptimizedQuantumImplementation}"
    row += f"& 41496 & 8116 & 409520 & 41392 & 11837 & 321 & 13320216"
    row += f"& 41496 & 784740 & 289680 & 1284 & 53280864"
    row += "\\\\"
    print(row)

    row = "HIGHT 64/128~\\cite{jang2022ParallelQuantumAddition}"
    row += "& 228 & 4496 & 22614 & 5824 & 2479 & - & - & - & - & - & - & - "
    row += "\\\\"
    print(row)


def print_comparison_ciphers_oracle_measures():
    # Jaques
    row = "AES-128~\\cite{jaques2019implementing}"
    row += f"& 12 & 83 & 75 & 88 & 157 "
    row += f"& 12 & 79 & 71 & 83 & 151 "
    row += "\\\\"
    print(row)
    # Table 9 10
    iters = 64 + np.log2(0.58)
    # Note that it does not uses depth, but Toffoli depth
    row = (
        "Camellia-128~\\cite{lin2023FurtherInsightsConstructing}\\TblrNote{$\\lozenge$}"
    )
    # To the Tab.9 measures, we add 128 x for the ctx; 128 * 2 for the
    # decomposition of the multi-controlled phase flips into CCNOT; lb(lb(128)*2) ~= 4 for the depth
    # of the phase flip operator;
    w = round(np.log2(388))
    g = round(np.log2(3566 + 128 + 39600 + 10816 + 128) + iters + 1)
    d = round(np.log2(5284 + np.log2(128)) + iters + 1)
    dw = round(np.log2(2050192 + 128 * 2) + iters + 1)
    row += f"& {w} & {g} & {d} & {dw} & {d + g}"
    # To the Tab.10 measures, we add 128 T gates for the QAND decomposition of Toffoli
    # gates; lb(lb(128)) ~= 3 for the T-depth of the phase flip operator using
    # QAND and QAND^\dagger;
    w = round(np.log2(388))
    g = round(np.log2(75712 + 128) + iters + 1)
    d = round(np.log2(15852 + np.log2(128)) + iters + 1)
    dw = round(np.log2(6150576 + np.log2(128)) + iters + 1)
    row += f"& {w} & {g} & {d} & {dw} & {d + g}"
    row += "\\\\"
    print(row)
    # To the Tab.11 measures, we add 128 T gates for the decomposition of the
    # CCNOT phase flips in QAND; lb(lb(128)) ~= 3 for the T-depth of the phase
    # flip operator; for
    row = "Camellia-128~\\cite{lin2023FurtherInsightsConstructing}\\TblrNote{$\\blacklozenge$}"
    row += "& - & - & - & - & - "
    w = round(np.log2(992))
    # 32 because we want to account only for 64 T gates
    g = round(np.log2(24960 + 32) + iters + 1)
    d = round(np.log(92 + np.log2(128)) + iters + 1)
    dw = round(np.log2(6150576 + np.log2(128)) + iters + 1)
    row += f"& {w} & {g} & {d} & {dw} & {d + g}"
    row += "\\\\"
    print(row)
    row = "SEED\\cite{oh2023OptimizedQuantumImplementation}"
    row += f"& 15 & 84 & 79 & 95 & 164 "
    # Tab. 2
    _t = np.log2(289680)
    _td = np.log2(1284)
    _w = np.log2(41496)
    _fix = 1.65 # 2*2*pi/4
    row += f"& {round(_w)} & {round(_t + _fix + 64)} & {round(_td + _fix + 64)} & {round(_td  + _fix + 64 + _w)} & {round(_td  + _fix + 64 + _t)} "
    row += "\\\\"
    print(row)

    row = "HIGHT 64/128~\\cite{jang2022ParallelQuantumAddition}"
    row += "& 9 & 82 & 75 & 85 & 158 "
    # Tab. 3
    _w = np.log2(457)
    _t = np.log2(294808)
    _td = np.log2(4959)
    _fix = 1.65 # 2*2*pi/4
    row += f"& {round(_w)} & {round(_t + _fix + 64)} & {round(_td + _fix + 64)} & {round(_td  + _fix + 64 + _w)} & {round(_td  + _fix + 64 + _t)} "
    row += "\\\\"
    print(row)


def main():
    # ex_s1()

    print("*" * 79)
    print("S-boxes parallel measures")
    print("*" * 79)
    uf_measures = get_sboxes_parallel_measures()
    print(uf_measures)

    print("*" * 79)
    print("S-boxes sequential measures")
    print("*" * 79)
    uf_measures = get_sboxes_sequential_measures()
    print(uf_measures)

    print("*" * 79)
    print("Encryption circuit")
    print("*" * 79)
    # header = f"Variant & W & X & CX & CCX & D & D-CCX & D-$\\times$W & W & Clifford & T & T-D & T-D$\\times$W\\\\"
    header = "Variant & W & X & CX & Toffoli & Full depth & Toffoli Depth & W & Clifford & T & T Depth\\\\"
    print(header)
    print("\\midrule")
    for n_keys in range(1, 4):
        for suffix, res in zip(
            ("\\TblrNote{$\\lozenge$}", "\\TblrNote{$\\blacklozenge$}"),
            (
                get_encryption_measures_sequential(n_keys),
                get_encryption_measures_parallel(n_keys),
            ),
        ):
            overall, overall2, cliffordt, cliffordt2 = res
            if n_keys == 1:
                head = f"DES{suffix}"
            elif n_keys == 2:
                head = f"3DES2{suffix}"
            elif n_keys == 3:
                head = f"3DES3{suffix}"
            row = f"{head} "
            row += f"& {round(overall['W'])}  "
            row += f"& {round(overall['G']['X'] )}  "
            row += f"& {round(overall['G']['CNOT'] )}  "
            row += f"& {round(overall['G']['C-C-X'] )}  "
            row += f"& {round(overall['D'] )}  "
            row += f"& {round(overall['D-CCNOT'] )}  "
            row += f"& {round(overall['D-CCNOT']  + overall2['W'])}  "

            row += f"& {round(cliffordt['W'])}  "
            row += f"& {round(cliffordt['nT'] )}  "
            row += f"& {round(cliffordt['T'] )}  "
            row += f"& {round(cliffordt['D-T'] )}"
            row += f"& {round(cliffordt['D-T']  + overall2['W'])}"
            row += "\\\\"
            print(row)
    print("\\midrule")

    print_comparison_ciphers_encryption_measures()

    print("*" * 79)
    print("Full Grover")
    print("*" * 79)
    # header = f"Variant & W & X & CX & CCX & D & {{Total D\\\\$\\cdot$W}} & W & T & T-D & T-D$\\cdot$W\\\\"
    # header = f"Variant & W & {{Total\\\\Gates}} & {{Total\\\\Depth}} & {{Total Depth\\\\$\\cdot$Width}} & {{NIST\\\\Compl.}} & W & {{T}} & {{T-D}} & {{T-D\\\\$\\cdot$W}} & {{NIST\\\\Compl.}} \\\\"
    header = f"Variant & W & G & D & D$\\cdot$W & {{NIST\\\\Compl.}} & W & T & T-D & T-D$\\cdot$W & {{NIST\\\\Compl.}} \\\\"
    print(header)
    print("\\midrule")
    for n_keys in range(1, 4):
        for suffix, res in zip(
            ("\\TblrNote{$\\lozenge$}", "\\TblrNote{$\\blacklozenge$}"),
            (
                get_oracle_sequential_measures(n_keys),
                get_oracle_parallel_measures(n_keys),
            ),
        ):
            overall, overall2, cliffordt, cliffordt2 = res
            if n_keys == 1:
                head = f"DES{suffix}"
            elif n_keys == 2:
                head = f"3DES2{suffix}"
            elif n_keys == 3:
                head = f"3DES3{suffix}"
            row = f"{head} "
            row += f"& {round(overall2['W'])} "
            # row += f"& {round(overall2['G']['X'] )}"
            # row += f"& {round(overall2['G']['CNOT'] )}"
            # row += f"& {round(overall2['G']['C-C-X'] )}"
            row += f"& {round(overall2['G-sum'] )} "
            row += f"& {round(overall2['D'] )} "
            row += f"& {round(overall2['D']  + overall2['W'])} "
            row += f"& {round(overall2['D'] + overall2['G-sum'])}"

            row += f"& {round(cliffordt2['W'])} "
            row += f"& {round(cliffordt2['T'] )} "
            row += f"& {round(cliffordt2['D-T'] )} "
            row += f"& {round(cliffordt2['D-T']  + overall2['W'])}"
            row += f"& {round(cliffordt2['D-T'] + overall2['G-sum'])}\\\\"
            print(row)

    n_keys = 2
    for suffix2, mem_cost_access in zip(
        ("$\\sqrt[3]{M}$", "$\\sqrt[2]{M}$"), (np.power(2, 56 / 3), np.power(2, 56 / 2))
    ):
        for suffix, res in zip(
            ("\\TblrNote{$\\lozenge$}", "\\TblrNote{$\\blacklozenge$}"),
            (
                get_oracle_sequential_measures(n_keys),
                get_oracle_parallel_measures(n_keys),
            ),
        ):
            head = f"3DES3{suffix}-{suffix2}"
            overall, overall2, cliffordt, cliffordt2 = res
            # MITM strategy, with a QRACM of size M=2^56
            # sqrt[3]{M} depth
            iters = get_iters(2)
            # get the depth of a single compute
            depth_compute = overall2["D"] - (iters + 1)
            # add the mem cost access
            depth_compute_new = (
                np.log2(2**depth_compute + mem_cost_access) + iters + 1
            )
            overall2["D"] = depth_compute_new
            depth_diff = depth_compute_new - depth_compute
            cliffordt2["D-T"] += depth_diff

            row = f"{head} "
            row += f"& {round(overall2['W'])} "
            # row += f"& {round(overall2['G']['X'] )}"
            # row += f"& {round(overall2['G']['CNOT'] )}"
            # row += f"& {round(overall2['G']['C-C-X'] )}"
            row += f"& {round(overall2['G-sum'] )} "
            row += f"& {round(overall2['D'] )} "
            row += f"& {round(overall2['D']  + overall2['W'])} "
            row += f"& {round(overall2['D'] + overall2['G-sum'])}"

            row += f"& {round(cliffordt2['W'])} "
            row += f"& {round(cliffordt2['T'] )} "
            row += f"& {round(cliffordt2['D-T'] )} "
            row += f"& {round(cliffordt2['D-T']  + overall2['W'])}"
            row += f"& {round(cliffordt2['D-T'] + overall2['G-sum'])}\\\\"
            print(row)

    # Others
    print("\\midrule")

    print_comparison_ciphers_oracle_measures()


if __name__ == "__main__":
    main()
