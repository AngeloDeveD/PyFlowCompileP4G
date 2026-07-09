from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BitId:
    """Named or numeric P4G bit identifier.

    Use named bits for readable generated FlowScript. A BitId with name="MOD_DONE"
    renders as MOD_DONE and is registered as a const int by the project when used
    by SDK helpers.
    """

    value: int
    name: str | None = None
    reason: str | None = None
    safe: bool = False

    def render(self) -> str:
        """Render the bit as its constant name when available, otherwise as a number."""
        return self.name or str(self.value)


def bit(value: int, *, name: str | None = None, reason: str | None = None, safe: bool = False) -> BitId:
    """Create a BitId for use with bitChk, bit_on, bit_off, and related helpers.

    Set name when you want generated FlowScript to use a readable const int.
    Set safe=True when you already know this bit is safe for the mod to use.
    """
    return BitId(value=value, name=name, reason=reason, safe=safe)


@dataclass(frozen=True)
class EventId:
    """Three-part P4G event identifier used by CALL_EVENT."""

    major: int
    minor: int
    sub: int = 0

    def args(self) -> tuple[int, int, int]:
        """Return values in the order expected by CALL_EVENT."""
        return self.major, self.minor, self.sub


@dataclass(frozen=True)
class FieldId:
    """Four-part P4G field identifier used by CALL_FIELD."""

    major: int
    minor: int
    location: int = 0
    weather: int = 0

    def args(self) -> tuple[int, int, int, int]:
        """Return values in the order expected by CALL_FIELD."""
        return self.major, self.minor, self.location, self.weather


@dataclass(frozen=True)
class Bustup:
    """MessageScript bustup portrait tag.

    Bustups are rendered into message text as [bup character expression costume
    position]. They are passed to Message.line(..., bustup=Bustup(...)).
    """

    character_id: int
    expression_id: int
    costume_id: int = 65535
    position: int = 1

    def render(self) -> str:
        """Render this bustup as a MessageScript [bup ...] tag."""
        return f"[bup {self.character_id} {self.expression_id} {self.costume_id} {self.position}]"


@dataclass(frozen=True)
class VoiceCue:
    """MessageScript voice playback tag.

    Voice cues are rendered into message text as [vp event_major event_minor
    event_sub cue_id]. They are passed to Message.line(..., voice=VoiceCue(...)).
    """

    event_major: int
    event_minor: int
    event_sub: int
    cue_id: int

    def render(self) -> str:
        """Render this voice cue as a MessageScript [vp ...] tag."""
        return f"[vp {self.event_major} {self.event_minor} {self.event_sub} {self.cue_id}]"