from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .exceptions import BitAllocationError


DEFAULT_MOD_BIT_START = 9000
DEFAULT_MOD_BIT_END = 9999


@dataclass(frozen=True)
class BitReservation:
    name: str
    value: int
    range_start: int
    range_end: int
    reason: str | None = None
    safe: bool = True

    def to_dict(self) -> dict[str, int | str | bool | None]:
        return {
            "name": self.name,
            "value": self.value,
            "range_start": self.range_start,
            "range_end": self.range_end,
            "reason": self.reason,
            "safe": self.safe,
        }


def allocate_bit(
    *,
    analyzer: Any | None,
    range_start: int,
    range_end: int,
    reserved: set[int] | None = None,
    preferred: int | None = None,
) -> int:
    if range_start > range_end:
        raise BitAllocationError(f"Invalid bit range: {range_start}..{range_end}")

    reserved_values = set(reserved or set())
    occupied = analyzer.used_bit_ids() if analyzer is not None and hasattr(analyzer, "used_bit_ids") else set()
    unavailable = occupied | reserved_values

    if preferred is not None and range_start <= preferred <= range_end and preferred not in unavailable:
        return preferred

    for candidate in range(range_start, range_end + 1):
        if candidate not in unavailable:
            return candidate

    raise BitAllocationError(f"No free bit found in range {range_start}..{range_end}")
