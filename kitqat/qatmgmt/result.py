from typing import TYPE_CHECKING, Mapping, cast

import numpy as np
from bitarray import bitarray
from kitqat.qatmgmt.program import QArray
from kitqat.utils.bits.conversion import (get_bitstring_array,
                                          get_ints_from_bitarray)

if TYPE_CHECKING:
    from qat.core.wrappers.result import Result


def get_state_vector_from_result(res: "Result", nqubits: int) -> np.array:
    state_vec = np.zeros(2**nqubits, dtype=np.complex256)
    for sample in res:
        state_dec = sample.state.state
        state_vec[state_dec] = sample.amplitude
    return state_vec


def get_sample_for_basis_dec_from_result(res: "Result",
                                         basis_state_dec: int,
                                         little_endian=False):
    attr = "lsb_int" if little_endian else "int"
    for sample in res:
        if getattr(sample.state, attr) == basis_state_dec:
            return sample
        # This is true if we assume that the samples are
        # put in the result list in order
        # Apparently NOT true in the QLM, so full search is needed
        # elif sample.state.state > basis_state_dec:
        #     return None
    return None


def get_sample_for_basis_str_from_result(res: "Result", basis_str_dec: int):
    for sample in res:
        if sample.state.bitstring == basis_str_dec:
            return sample
    return None


# ------------------------------------------------------------------ #
# Value decoding for CircuitLike objects
# ------------------------------------------------------------------ #


def bitstring_to_register_map(
    bitstring: str,
    name_to_qarray: dict[str, QArray],
) -> dict[str, bitarray]:
    """Slice a full bitstring back into named registers.

    Inverse of :meth:`register_map_to_bitstring`.
    """
    bits = bitarray(bitstring)
    return {name: bits[qa.slic] for name, qa in name_to_qarray.items()}


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
            raise KeyError(f"Ancilla '{name}' not found. "
                           f"Available ancillae: {list(self._ancillae)}")

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
                f"but accessed as {expected_qtype.__name__!r}.")
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
                f"use the appropriate as_*_list accessor instead.")
        return cast(bitarray, self._data[name])


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
            result[name] = get_ints_from_bitarray(bits.tolist(), qa.n, qa.m,
                                                  False)
        else:
            raise TypeError(f"Unknown qtype: {qa.qtype!r}")
    return DecodedStates(result, name_to_qarray, ancillae)
