"""Reversible circuit simulation.

Public surface
--------------
RGate        – gate enum (NOT, SWAP, RESET, I)
RProgram     – stateful bit-register machine
RSimulator   – stateless helpers: build from any source, simulate, inspect
CircuitLike  – Protocol for ProgramWrapper / QRoutineWrapper duck-typing
"""

from __future__ import annotations

import logging
from typing import Literal, overload
from bitarray import bitarray
import operator
from collections.abc import Mapping
from enum import Enum, auto
from typing import (TYPE_CHECKING, Optional, Protocol, Sequence, Union, cast,
                    runtime_checkable)

from bitarray import bitarray
from qatext.qatmgmt.program import QArray
from qatext.utils.bits.conversion import (get_bitstring_array,
                                          get_ints_from_bitarray)

if TYPE_CHECKING:
    from qat.core.wrappers.circuit import Circuit
    from qat.lang.AQASM.routines import QRoutine
    from qat.lang.AQASM.program import Program

from bitarray import bitarray, util

class DecodedStates(Mapping[str, object]):
    """Typed wrapper around decoded register states.

    Validates the expected type against the QArray's qtype at access time,
    giving a clear error instead of a cryptic AttributeError downstream.
    """

    def __init__(
        self,
        data: dict[str, object],
        name_to_qarray: dict[str, QArray],
        ancillae: dict[str, bitarray] | None = None,
    ):
        self._data = data
        self._nmap = name_to_qarray
        self._ancillae: dict[str, bitarray] = ancillae or {}

    def get_ancilla(self, name: str) -> bitarray:
        """Return the raw bitarray for a compiler-generated ancilla register."""
        try:
            return self._ancillae[name]
        except KeyError:
            raise KeyError(
                f"Ancilla '{name}' not found. "
                f"Available ancillae: {list(self._ancillae)}"
            )

    def ancillae(self) -> dict[str, bitarray]:
        """Return all compiler-generated ancilla registers."""
        return dict(self._ancillae)
    def __getitem__(self, name: str) -> object:
        return self._data[name]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self) -> str:
        return f"DecodedStates({self._data!r})"

    def _get_typed(self, name: str, expected_qtype: type) -> object:
        qa = self._nmap.get(name)
        if qa is None:
            raise KeyError(f"Register '{name}' not found in name_to_qarray.")
        if not qa.unknown_size and qa.qtype != expected_qtype:
            raise TypeError(
                f"Register '{name}' has qtype={qa.qtype.__name__!r}, "
                f"but accessed as {expected_qtype.__name__!r}."
            )
        return self._data[name]

    def as_bitarray_list(self, name: str) -> list[bitarray]:
        return cast(list[bitarray], self._get_typed(name, bool))

    def as_int_list(self, name: str) -> list[int]:
        return cast(list[int], self._get_typed(name, int))

    def as_bitstring_list(self, name: str) -> list[str]:
        return cast(list[str], self._get_typed(name, str))

    def as_bitarray(self, name: str) -> bitarray:
        """For unknown_size registers that are returned as a raw bitarray."""
        qa = self._nmap.get(name)
        if qa is None:
            raise KeyError(f"Register '{name}' not found in name_to_qarray.")
        if not qa.unknown_size:
            raise TypeError(
                f"Register '{name}' has known size and qtype={qa.qtype.__name__!r}; "
                f"use the appropriate as_*_list accessor instead."
            )
        return cast(bitarray, self._data[name])

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class CircuitLike(Protocol):
    """Anything that can produce a Circuit and owns a name→QArray map.

    Both ProgramWrapper and QRoutineWrapper satisfy this contract.
    """

    _name_to_qarray: dict[str, QArray]

    def to_circ(self, *, link: Optional[list], inline: bool) -> "Circuit": ...


# ---------------------------------------------------------------------------
# Gate enum
# ---------------------------------------------------------------------------

class RGate(Enum):
    """Reversible gate: NOT, SWAP, RESET, or identity I."""

    NOT = auto()
    SWAP = auto()
    RESET = auto()
    I = auto()


# ---------------------------------------------------------------------------
# RProgram – the stateful bit machine
# ---------------------------------------------------------------------------

class RProgram:
    """A reversible equivalent of the qat Program object.

    Gates are applied *immediately* onto the internal bitarray when
    :meth:`apply` is called.  Use :class:`RSimulator` to build and run
    an ``RProgram`` from a higher-level source (Circuit, ProgramWrapper…).
    """

    _REV_GATE_SUFFIXES = ("X", "NOT", "SWAP", "I")

    # ------------------------------------------------------------------ #
    # Construction / allocation                                            #
    # ------------------------------------------------------------------ #

    def __init__(self) -> None:
        self.ops: list = []
        self.rbits: bitarray = bitarray()
        self.rregs: dict[str, QArray] = {}

    def ralloc(self, n: int = 1, name: Optional[str] = None) -> None:
        """Allocate a register of *n* reversible bits.

        Parameters
        ----------
        n:    number of bits (default 1).
        name: optional register name; must be unique.
        """
        slic = slice(len(self.rbits), len(self.rbits) + n)
        if name is None:
            name = str(slic)[6:].replace(", ", "_").replace(")", "")
        elif name in self.rregs:
            raise ValueError(f"Register name '{name}' already exists.")
        self.rregs[name] = QArray(slic, 1, n, None, str)
        self.rbits.extend(util.zeros(n))

    # ------------------------------------------------------------------ #
    # Gate application                                                     #
    # ------------------------------------------------------------------ #

    def apply(self, gate: RGate, *rbits: int) -> None:
        """Apply *gate* on *rbits*.

        Convention: first indices are controls, last index/indices are targets.
        """
        if not self.rbits:
            raise AttributeError("No bits allocated – call ralloc() first.")

        ntrgts = 2 if gate == RGate.SWAP else 1
        trgts = rbits[-ntrgts:]
        ctrls = rbits[: len(rbits) - ntrgts]

        if len(trgts) + len(ctrls) != len(rbits):
            raise ValueError(f"Wrong number of rbits: got {len(rbits)}.")
        if not set(ctrls).isdisjoint(set(trgts)):
            raise ValueError("Control and target sets must be disjoint.")

        self.ops.append((gate, *ctrls, *trgts))

        # Evaluate control condition
        active = (
            not ctrls
            or (len(ctrls) == 1 and operator.itemgetter(*ctrls)(self.rbits) == 1)
            or (len(ctrls) > 1 and all(operator.itemgetter(*ctrls)(self.rbits)))
        )
        if not active:
            return

        if gate == RGate.NOT:
            for t in trgts:
                self.rbits.invert(t)
        elif gate == RGate.SWAP:
            self.rbits[trgts[1]], self.rbits[trgts[0]] = (
                self.rbits[trgts[0]],
                self.rbits[trgts[1]],
            )
        elif gate == RGate.RESET:
            self.rbits[trgts[0]] = 0
        # RGate.I → identity, nothing to do

    def _apply_gate_from_name(self, gatename: str, rbits: Sequence[int]) -> None:
        """Dispatch a gate by its string name.

        Accepted: SWAP, I, X, NOT, CNOT, C-NOT, CX, C-X,
                  CCNOT, C-C-NOT, C-CNOT, C-C-X, CCX.
        """
        if gatename == "SWAP":
            rgate, trgts, ctrls = RGate.SWAP, list(rbits[-2:]), list(rbits[:-2])
        elif gatename == "I":
            rgate, trgts, ctrls = RGate.I, [rbits[-1]], list(rbits[:-1])
        elif gatename in {
            "X", "NOT", "CNOT", "C-NOT", "C-X", "CX",
            "C-C-NOT", "CCNOT", "C-CNOT", "C-C-X", "CCX",
        }:
            rgate, trgts, ctrls = RGate.NOT, [rbits[-1]], list(rbits[:-1])
        else:
            raise AttributeError(f"Unknown reversible gate: '{gatename}'.")

        self.apply(rgate, *ctrls, *trgts)

    # ------------------------------------------------------------------ #
    # Gate application from high-level sources                            #
    # ------------------------------------------------------------------ #

    def apply_gates_from_circuit(
        self,
        top_circ: "Circuit",
        operation_circ: "Circuit",
    ) -> None:
        """Apply all gates from *operation_circ* (embedded in *top_circ*)."""
        for op in operation_circ:
            gatename = op.gate
            if gatename is None:
                if op.type == 2:  # reset
                    self.apply(RGate.RESET, op.qbits)
                # type == 1 → measure, NOP
                continue

            subcirc = top_circ.gateDic[gatename].circuit_implementation
            if subcirc is not None:
                self.apply_gates_from_circuit(top_circ, subcirc)
            else:
                if not gatename.endswith(self._REV_GATE_SUFFIXES):
                    if gatename.startswith("_"):
                        gatename = top_circ.gateDic[gatename].subgate
                    else:
                        raise AttributeError(
                            "Only X, SWAP and their controlled versions are "
                            f"accepted; got '{gatename}'."
                        )
                self._apply_gate_from_name(gatename, op.qbits)

    def apply_gates_from_qroutine(
        self,
        qroutine: "QRoutine",
        qbits: Sequence[int] = (),
    ) -> None:
        """Apply all gates from a QRoutine.

        Note: pass the bare ``QRoutine``, not the AbstractGate wrapper
        (use the tilde operator ``~gate`` to unwrap if needed).
        """
        if not qbits:
            qbits = range(qroutine.arity)
        elif len(qbits) < qroutine.arity:
            raise ValueError(f"Too few qbits supplied: {len(qbits)}.")

        mapping: dict[int, int] = dict(zip(range(qroutine.arity), qbits))
        for op in qroutine.op_list:
            op_qbits = [mapping[i] for i in op.args]
            name = op.gate.name or (
                op.gate.subgate.name if op.gate.subgate is not None else None
            )
            if name is not None:
                self._apply_gate_from_name(name, op_qbits)
            else:
                self.apply_gates_from_qroutine(op.gate, op_qbits)

    # ------------------------------------------------------------------ #
    # Result accessors                                                     #
    # ------------------------------------------------------------------ #

    def get_result(self) -> str:
        """Return the full bit-state as a '0'/'1' string."""
        return self.rbits.to01()

    def get_result_by_name(self) -> dict[str, bitarray]:
        """Return a ``{register_name: bitarray}`` dict for all registers."""
        return {name: self.rbits[qa.slic] for name, qa in self.rregs.items()}

    def filter_result_by_name(self, *names: str) -> dict[str, bitarray]:
        """Like :meth:`get_result_by_name` but restricted to *names*."""
        return {
            name: self.rbits[qa.slic]
            for name, qa in self.rregs.items()
            if name in names
        }


# ---------------------------------------------------------------------------
# RSimulator – stateless factory + inspection helpers
# ---------------------------------------------------------------------------

class RSimulator:
    """Stateless helpers for building and running :class:`RProgram` instances.

    All methods are static; the class is a namespace, not meant to be
    instantiated.
    """

    # ------------------------------------------------------------------ #
    # Building an RProgram from various sources                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def from_circuit(
        circ: "Circuit",
        name_to_qarray: dict[str, QArray] | None = None,
    ) -> RProgram:
        """Build *and* run an :class:`RProgram` from a qat ``Circuit``.

        Parameters
        ----------
        circ:
            The (already inlined) circuit to simulate.
        name_to_qarray:
            Optional mapping from register names to :class:`QArray` objects.
            When provided the resulting ``RProgram.rregs`` will reflect those
            names so that :meth:`~RProgram.get_result_by_name` returns
            meaningful keys.
        """
        name_to_qarray = name_to_qarray or {}
        rpr = RProgram()

        slic_to_name: dict[slice, str] = {
            qa.slic: name for name, qa in name_to_qarray.items()
        }
        for qr in circ.qregs:
            slic = slice(qr.start, qr.start + qr.length)
            rpr.ralloc(qr.length, slic_to_name.get(slic))

        # Ancillae automatically generated from subroutines
        qdiff = circ.nbqbits - len(rpr.rbits)
        if qdiff > 0:
            rpr.ralloc(qdiff, "auto_ancillae")

        rpr.apply_gates_from_circuit(circ, circ)
        return rpr

    @staticmethod
    def from_circuit_like(
        source: CircuitLike,
        link: Optional[list] = None,
    ) -> RProgram:
        """Build *and* run an :class:`RProgram` from any :class:`CircuitLike`.

        Works transparently with :class:`~qatext.qatmgmt.program.ProgramWrapper`
        and :class:`~qatext.qatmgmt.routines.QRoutineWrapper`.
        """
        circ = source.to_circ(link=link, inline=True)
        rpr = RSimulator.from_circuit(circ, source._name_to_qarray)
        # Merge rather than overwrite: auto_ancillae (and any other registers
        # allocated during circuit compilation) must be preserved. They cannot
        # live in source._name_to_qarray because ProgramWrapper has no
        # knowledge of them — they are a side-effect of to_circ() / inlining.
        # The only place that knows about them is rpr.rregs after
        # alloc_from_circuit has run, so the merge must happen here and not
        # earlier. User-named registers take priority in case of key collision.
        rpr.rregs = {**rpr.rregs, **source._name_to_qarray}
        return rpr

    # ------------------------------------------------------------------ #
    # Simulation entry points                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def simulate_circuit(
        circ: "Circuit",
        name_to_qarray: dict[str, QArray] | None = None,
    ) -> dict[str, bitarray] | str:
        """Simulate *circ* and return register states."""
        rpr = RSimulator.from_circuit(circ, name_to_qarray)
        return rpr.get_result_by_name()

    @staticmethod
    def simulate_circuit_as_bitstring(
        circ: "Circuit",
        name_to_qarray: dict[str, QArray] | None = None,
    ) -> dict[str, bitarray] | str:
        """Simulate *circ* and return register states."""
        rpr = RSimulator.from_circuit(circ, name_to_qarray)
        return rpr.get_result()

    @staticmethod
    def simulate(
        source: CircuitLike,
        link: Optional[list] = None,
    ) -> dict[str, bitarray]:
        rpr = RSimulator.from_circuit_like(source, link=link)
        return rpr.get_result_by_name()

    @staticmethod
    def simulate_as_bitstring(
        source: CircuitLike,
        link: Optional[list] = None,
    ) -> str:
        rpr = RSimulator.from_circuit_like(source, link=link)
        return rpr.get_result()

    @staticmethod
    def bitstring_to_register_map(
        bitstring: str,
        name_to_qarray: dict[str, QArray],
    ) -> dict[str, bitarray]:
        """Slice a full bitstring back into named registers.

        Inverse of :meth:`register_map_to_bitstring`.
        """
        bits = bitarray(bitstring)
        return {name: bits[qa.slic] for name, qa in name_to_qarray.items()}

    @staticmethod
    def register_map_to_bitstring(
        register_map: dict[str, bitarray],
        name_to_qarray: dict[str, QArray],
    ) -> str:
        """Reconstruct the full bitstring from named register slices.

        Inverse of :meth:`bitstring_to_register_map`.
        """
        # Determine total length from the highest slice endpoint
        total = max(qa.slic.stop for qa in name_to_qarray.values())
        bits = bitarray(total)
        bits.setall(0)
        for name, qa in name_to_qarray.items():
            bits[qa.slic] = register_map[name]
        return bits.to01()

    # ------------------------------------------------------------------ #
    # Value decoding                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def decode_states(
        states: dict[str, bitarray],
        name_to_qarray: dict[str, QArray],
    ) -> DecodedStates:
        result: dict[str, object] = {}
        ancillae: dict[str, bitarray] = {}
        for name, bits in states.items():
            if name not in name_to_qarray:
                # compiler-generated register (auto_ancillae, slice-named regs…)
                # kept as raw bitarray since there is no qtype metadata for them
                ancillae[name] = bits
                continue
            qa = name_to_qarray[name]
            if qa.unknown_size:
                result[name] = bits
            elif qa.qtype == str:
                assert qa.n is not None and qa.m is not None
                result[name] = get_bitstring_array(bits.to01(), qa.n, qa.m)
            elif qa.qtype == bool:
                result[name] = bits
            elif qa.qtype == int:
                assert qa.n is not None and qa.m is not None
                result[name] = get_ints_from_bitarray(bits.tolist(), qa.n, qa.m, False)
            else:
                raise TypeError(f"Unknown qtype: {qa.qtype!r}")
        return DecodedStates(result, name_to_qarray, ancillae)

    # ------------------------------------------------------------------ #
    # Simulate and Value decoding                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def simulate_and_decode(
        source: CircuitLike,
        link: Optional[list] = None,
    ) -> DecodedStates:
        nmap = source._name_to_qarray
        return RSimulator.decode_states(RSimulator.simulate(source, link=link), nmap)

    # ------------------------------------------------------------------ #
    # Inspection / pretty-printing                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _format_inspection(
        circ: "Circuit",
        rpr: RProgram,
        name_to_qarray: dict[str, QArray],
    ) -> str:
        """Shared formatting logic for all inspect_* helpers."""
        state = rpr.get_result_by_name()
        decoded = RSimulator.decode_states(state, name_to_qarray)

        lines = [
            "",
            f"n qbits  {circ.nbqbits}",
            f"n rbits  {len(rpr.rbits)}",
            f"state    {' ' * 25}->  {rpr.rbits}",
        ]
        for name, value in decoded.items():
            slic = name_to_qarray[name].slic
            lines.append(f"  {name:<20} [{slic}] ->  {value}")

        return "\n".join(lines)

    @staticmethod
    def inspect_circuit(
        circ: "Circuit",
        name_to_qarray: dict[str, QArray] | None = None,
    ) -> str:
        """Simulate *circ* and return a human-readable state summary."""
        name_to_qarray = name_to_qarray or {}
        rpr = RSimulator.from_circuit(circ, name_to_qarray)
        # rpr.rregs = name_to_qarray
        rpr.rregs = {**rpr.rregs, **name_to_qarray}  # merge, don't overwrite
        return RSimulator._format_inspection(circ, rpr, name_to_qarray)

    @staticmethod
    def inspect_program(
        pr: "Program",
        name_to_qarray: dict[str, QArray] | None = None,
        **to_circ_kwargs,
    ) -> str:
        """Simulate a bare qat Program and return a human-readable state summary.

        Parameters
        ----------
        pr:
            The qat Program to inspect.
        name_to_qarray:
            Optional register name mapping. Without it registers are labelled
            by their auto-generated slice names.
        **to_circ_kwargs:
            Forwarded verbatim to ``pr.to_circ()`` — use this for
            ``include_matrices=False``, ``submatrices_only=True``, ``link=…``, etc.
        """
        name_to_qarray = name_to_qarray or {}
        circ = pr.to_circ(**to_circ_kwargs)
        rpr = RSimulator.from_circuit(circ, name_to_qarray)
        # rpr.rregs = name_to_qarray
        rpr.rregs = {**rpr.rregs, **name_to_qarray}  # merge, don't overwrite
        return RSimulator._format_inspection(circ, rpr, name_to_qarray)

    @staticmethod
    def inspect(
        source: CircuitLike,
        link: Optional[list] = None,
    ) -> str:
        """Simulate any :class:`CircuitLike` and return a human-readable summary.

        Works with :class:`~qatext.qatmgmt.program.ProgramWrapper` and
        :class:`~qatext.qatmgmt.routines.QRoutineWrapper`.
        """
        circ = source.to_circ(link=link, inline=True)
        rpr = RSimulator.from_circuit(circ, source._name_to_qarray)
        # rpr.rregs = source._name_to_qarray
        rpr.rregs = {**rpr.rregs, **source._name_to_qarray}  # merge, don't overwrite
        return RSimulator._format_inspection(circ, rpr, source._name_to_qarray)
