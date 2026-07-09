from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TimeSpan:
    """Calendar date span rendered as CHECK_TIME_SPAN(month, day, month, day).

    The name is kept for backward compatibility. The values are calendar dates,
    not clock time. New code can use checkTimeSpan(...) from the expression DSL
    when it needs comparison operators such as == 1.
    """

    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int

    def render_condition(self) -> str:
        """Render this date span as a complete FlowScript boolean condition."""
        return (
            "CHECK_TIME_SPAN("
            f"{self.start_hour}, {self.start_minute}, {self.end_hour}, {self.end_minute}"
            ") == 1"
        )

    def render_flow(self) -> str:
        """Render this object for APIs that accept expression-like values."""
        return self.render_condition()


@dataclass(frozen=True)
class Date:
    """Single in-game calendar date rendered through DATE_CHK(month, day)."""

    month: int
    day: int

    def render_condition(self) -> str:
        """Render this date as DATE_CHK(month, day) == 1."""
        return f"DATE_CHK({self.month}, {self.day}) == 1"

    def render_flow(self) -> str:
        """Render this object for APIs that accept expression-like values."""
        return self.render_condition()


def render_condition(condition: Any) -> str:
    """Render any supported condition object as FlowScript source code."""
    if hasattr(condition, "render_condition"):
        return condition.render_condition()
    if hasattr(condition, "render_flow"):
        return condition.render_flow()
    return str(condition)