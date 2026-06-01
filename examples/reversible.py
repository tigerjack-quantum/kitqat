"""RSimulator – usage examples
==============================

This file walks through the most common ways to use RSimulator, from the
simplest cases to the more advanced ones.  Each section is self-contained
and runnable.

Sections
--------
1.  Working directly with RProgram  (low-level, no qat circuits)
2.  Simulating a qat Program        (bare Program, no register names)
3.  Simulating a ProgramWrapper     (named registers, typed decoding)
4.  Inspecting state for debugging
5.  Accessing ancilla registers
6.  Converting between bitstring and register map

=============================================================================
Quick-reference summary
=============================================================================

Source type          | You want             | Call
---------------------|----------------------|--------------------------------
RProgram (manual)    | apply gates by hand  | rpr.apply(RGate.NOT, i)
Circuit              | full bitstring       | RSimulator.from_circuit(circ).get_result()
Circuit              | register dict        | RSimulator.simulate_circuit(circ, nmap)
Program              | full bitstring       | RSimulator.from_program(pr).get_result()
ProgramWrapper       | register dict        | RSimulator.simulate(prw)
ProgramWrapper       | typed values         | RSimulator.simulate_and_decode(prw)
Any of the above     | debug string         | RSimulator.inspect*(source)
bitstring → dict     | split by register    | RSimulator.bitstring_to_register_map(bs, nmap)
dict → bitstring     | reconstruct          | RSimulator.register_map_to_bitstring(d, nmap)

"""



from qat.lang.AQASM.gates import CCNOT, SWAP, X
from qat.lang.AQASM.program import Program

from qatext.qatmgmt.program import ProgramWrapper, QArray
from qatext.qpus.reversible import RGate, RProgram, RSimulator
from qatext.qroutines.qregs_mgmt.qregs_init import initialize_qureg_given_bitstring, initialize_qureg_given_int
from qatext.qroutines.qregs_mgmt.qregs_layout import swap_qreg_cells


# =============================================================================
# 1. Working directly with RProgram
#    Use this when you want to apply reversible gates by hand, without any
#    qat circuit involved.
# =============================================================================

def example_rprogram_basic():
    """Allocate bits, apply gates, read the result."""

    rpr = RProgram()
    rpr.ralloc(4, "reg")   # 4 bits, named "reg"

    # Apply a NOT on bit 0
    rpr.apply(RGate.NOT, 0)
    print(rpr.get_result())         # "1000"

    # CNOT: control=0, target=3  (fires because bit 0 is 1)
    rpr.apply(RGate.NOT, 0, 3)
    print(rpr.get_result())         # "1001"

    # SWAP bits 0 and 1
    rpr.apply(RGate.SWAP, 0, 1)
    print(rpr.get_result())         # "0101"  (bit 0 → 1, bit 1 → 0... wait)
    # Bit 0 was 1, bit 1 was 0 → after SWAP bit 0=0, bit 1=1
    # So result: "0101"

    # RESET bit 3 back to 0
    rpr.apply(RGate.RESET, 3)
    print(rpr.get_result())         # "0100"


def example_rprogram_named_registers():
    """Multiple named registers; read them back by name."""

    rpr = RProgram()
    rpr.ralloc(3, "a")
    rpr.ralloc(3, "b")

    rpr.apply(RGate.NOT, 0)   # flip bit 0 of "a"
    rpr.apply(RGate.NOT, 4)   # flip bit 1 of "b"  (global index 4)

    by_name = rpr.get_result_by_name()
    print(by_name["a"].to01())   # "100"
    print(by_name["b"].to01())   # "010"

    # Only get specific registers
    filtered = rpr.filter_result_by_name("a")
    print(filtered)              # {"a": bitarray("100")}


# =============================================================================
# 2. Simulating a bare qat Program
#    Use this when you have a Program built with anonymous qalloc calls and
#    you just want the full bitstring after simulation.
# =============================================================================

def example_bare_program():
    """Simulate a Program and get the full bitstring."""

    pr = Program()
    qr = pr.qalloc(4)
    pr.apply(X, qr[0])
    pr.apply(X, qr[1])
    pr.apply(CCNOT, qr[0], qr[1], qr[2])   # flips qr[2] since qr[0]=qr[1]=1

    circ = pr.to_circ()

    # Option A: full bitstring
    rpr = RSimulator.from_circuit(circ)
    print(rpr.get_result())      # "1110"

    # Option B: via from_program (skips the manual to_circ call)
    rpr2 = RSimulator.from_program(pr)
    print(rpr2.get_result())     # "1110"

    # Option C: with extra to_circ kwargs
    rpr3 = RSimulator.from_program(
        pr,
        include_matrices=False,
        submatrices_only=True,
    )
    print(rpr3.get_result())     # "1110"


# =============================================================================
# 3. Simulating a ProgramWrapper with named registers
#    This is the most common pattern for arithmetic circuits.
#    Named registers let you read back typed values (int, str, bool) instead
#    of raw bitstrings.
# =============================================================================

def example_program_wrapper():
    """Build a ProgramWrapper, name the registers, simulate and decode."""

    n = 4   # number of bits per integer

    prw = ProgramWrapper(Program())
    qr_a = prw.qarray_alloc(1, n, "a", int)   # one n-bit integer register
    qr_b = prw.qarray_alloc(1, n, "b", int)   # another

    # Load value 5 (= 0101 in binary) into "a"
    prw.apply(initialize_qureg_given_int(5, n, False), qr_a[0])
    # Load value 3 (= 0011) into "b"
    prw.apply(initialize_qureg_given_int(3, n, False), qr_b[0])

    # --- Simulate and get raw bitarrays per register ---
    states = RSimulator.simulate(prw)
    print(states["a"].to01())   # "0101"  (little-endian or big-endian depends on init gate)
    print(states["b"].to01())   # "0011"

    # --- Simulate and decode to typed Python values in one call ---
    decoded = RSimulator.simulate_and_decode(prw)
    print(decoded.as_int_list("a"))   # [5]
    print(decoded.as_int_list("b"))   # [3]

    # --- With a link (external arithmetic routines) ---
    # decoded = RSimulator.simulate_and_decode(prw, link=[some_lib])


def example_program_wrapper_multiple_registers():
    """Multiple registers of different types."""

    prw = ProgramWrapper(Program())

    # 2 integers of 4 bits each → qarray_alloc(n_elements, bits_each, name, type)
    qr_vals  = prw.qarray_alloc(2, 4, "values", int)
    # 1 boolean flag
    qr_flag  = prw.qarray_alloc(1, 1, "flag", bool)
    # 3 raw bitstrings of length 4
    qr_strs  = prw.qarray_alloc(3, 4, "labels", str)

    prw.apply(SWAP, qr_vals[0], qr_vals[-1])
    prw.apply(X, qr_flag[0])
    prw.apply(CCNOT, qr_flag[0], qr_strs[0], qr_strs[1])

    decoded = RSimulator.simulate_and_decode(prw)

    # Access by type — the accessor validates the qtype at runtime
    values = decoded.as_int_list("values")   # list[int], length 2
    flag   = decoded.as_bitarray("flag")     # raw bitarray, length 1
    labels = decoded.as_bitstring_list("labels")  # list[str], length 3

    print(values, flag, labels)


# =============================================================================
# 4. Inspecting state for debugging
#    inspect() / inspect_circuit() / inspect_program() return a formatted
#    string showing every register and its decoded value.  Ideal for logging.
# =============================================================================

def example_inspect():
    """Pretty-print the full state of a circuit for debugging."""

    pr = Program()
    qr = pr.qalloc(3)
    pr.apply(X, qr[0])
    pr.apply(X, qr[2])

    circ = pr.to_circ()

    # Inspect a compiled circuit (no name map → registers shown by slice)
    print(RSimulator.inspect_circuit(circ))
    # Output:
    #   n qbits  3
    #   n rbits  3
    #   state                             ->  bitarray('101')
    #     0_3_None             [slice(0,3)] ->  ...

    # Inspect with a name map
    nmap = {"my_reg": QArray(slice(0, 3), 1, 3, None, str)}
    print(RSimulator.inspect_circuit(circ, nmap))
    # Output:
    #   ...
    #     my_reg               [slice(0,3)] ->  ['101']


def example_inspect_program_wrapper():
    """Inspect a ProgramWrapper — names come from _name_to_qarray."""

    prw = ProgramWrapper(Program())
    qr = prw.qarray_alloc(1, 4, "result", int)
    # ... apply gates ...

    # Logs the full state with named registers
    print(RSimulator.inspect(prw))

    # With a link to external routines
    # print(RSimulator.inspect(prw, link=[some_lib]))

    # From a bare Program (with optional to_circ kwargs)
    pr = Program()
    # ... build pr ...
    print(RSimulator.inspect_program(pr, include_matrices=False))


# =============================================================================
# 5. Accessing ancilla registers
#    Compiler-generated ancillae (used internally by subroutines) are kept
#    separately from user-named registers and accessible via .ancillae().
# =============================================================================

def example_ancillae():
    """Check that ancillae are reset to zero after a computation."""

    prw = ProgramWrapper(Program())
    qr_a = prw.qarray_alloc(1, 4, "a", int)
    qr_b = prw.qarray_alloc(1, 4, "b", int)
    # some_gate internally allocates ancilla qubits
    prw.apply(initialize_qureg_given_bitstring('1001', False), qr_a)
    prw.apply(swap_qreg_cells(4), qr_a, qr_b)


    decoded = RSimulator.simulate_and_decode(prw)

    # Named registers — typed access
    print(decoded.as_int_list("a"))
    print(decoded.as_int_list("b"))

    # Compiler-generated registers — raw bitarrays
    anc = decoded.ancillae()
    print(anc)  # {"auto_ancillae": bitarray('000...'), ...}

    # Check all ancillae were properly uncomputed
    for name, bits in anc.items():
        assert not bits.any(), f"Ancilla '{name}' not reset to zero: {bits}"


# =============================================================================
# 6. Converting between bitstring and register map
#    Useful when you receive a bitstring from an external source (e.g. a QPU)
#    and want to split it into named registers, or vice versa.
# =============================================================================

def example_bitstring_conversion():
    """Round-trip between full bitstring and named register dict."""

    prw = ProgramWrapper(Program())
    prw.qarray_alloc(1, 4, "a", int)
    prw.qarray_alloc(1, 4, "b", int)
    nmap = prw._name_to_qarray

    # Simulate → get full bitstring
    rpr = RSimulator.from_circuit_like(prw)
    bitstring = rpr.get_result()              # e.g. "01010011"

    # Split bitstring into named registers
    register_map = RSimulator.bitstring_to_register_map(bitstring, nmap)
    print(register_map["a"].to01())           # "0101"
    print(register_map["b"].to01())           # "0011"

    # Reconstruct the full bitstring from the register map
    reconstructed = RSimulator.register_map_to_bitstring(register_map, nmap)
    assert reconstructed == bitstring         # round-trip is lossless

    # Typical use case: cross-check RSimulator against a QPU result
    # qpu_bitstring = sample.state.bitstring   # from QPU
    # qpu_registers = RSimulator.bitstring_to_register_map(qpu_bitstring, nmap)
    # sim_registers = RSimulator.simulate(prw)
    # assert qpu_registers == sim_registers


if __name__ == "__main__":
    sections = [
        ("1. RProgram – basic gates",               example_rprogram_basic),
        ("1. RProgram – named registers",           example_rprogram_named_registers),
        ("2. Bare Program – bitstring",             example_bare_program),
        ("3. ProgramWrapper – simulate_and_decode", example_program_wrapper),
        ("4. Inspect circuit",                      example_inspect),
        ("5. Ancillae",                             example_ancillae),
        ("6. Bitstring conversion",                 example_bitstring_conversion),
    ]
    for title, fn in sections:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        fn()
