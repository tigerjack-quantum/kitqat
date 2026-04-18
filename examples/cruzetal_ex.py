from qat.lang.AQASM.program import Program
from qatext.qroutines.hamming_weight_generate.cruzetal19 import w_state
from qat.lang.AQASM.gates import X
from qat.qpus import CLinalg


# ---- Demo & verification ----
if __name__ == "__main__":
    for n in [2, 3, 4, 6, 8, 16, 24, 48, 256]:
        print(f"n = {n}")
        prog = Program()
        qbits = prog.qalloc(n)
        prog.apply(w_state(n), qbits)
        circ = prog.to_circ()
        # circ = w_state_log_depth(n)
        print(circ.statistics())
        print("depth = ", circ.depth(default=1))
        if n > 25:
            print("No simulation")
            continue
        job = circ.to_job(nbshots=0)  # exact statevector
        qpu = CLinalg()
        result = qpu.submit(job)

        print(f"\n|W_{n}> (expected uniform prob = {1/n:.4f})")
        ok = True
        expected = 1 / n
        for sample in result:
            prob = sample.probability
            marker = "✓" if abs(prob - expected) < 1e-6 else f"✗ (expected {expected:.4f})"
            # Only print weight-1 states
            bits = format(int(str(sample.state), 2), f'0{n}b') if False else str(sample.state)
            print(f"  |{sample.state}>  prob = {prob:.6f}  {marker}")
            if abs(prob - expected) > 1e-4:
                ok = False
        print(f"  --> {'PASS' if ok else 'FAIL'}")
