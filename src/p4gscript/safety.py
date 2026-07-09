from __future__ import annotations

from .exceptions import P4GScriptError, SafetyError


BEGINNER = "beginner"
STANDARD = "standard"
EXPERT = "expert"

SAFETY_ALIASES = {
    BEGINNER: BEGINNER,
    "beginer": BEGINNER,
    "begginer": BEGINNER,
    STANDARD: STANDARD,
    "standart": STANDARD,
    "std": STANDARD,
    EXPERT: EXPERT,
}
SAFETY_CHOICES = tuple(SAFETY_ALIASES)

BEGINNER_ALLOWED_CALLS = frozenset(
    {
        "ADD_YEN",
        "BIT_CHK",
        "BIT_OFF",
        "BIT_ON",
        "CALL_EVENT",
        "CALL_FIELD",
        "CALL_FIELD_SAFE",
        "CHECK_TIME_SPAN",
        "CLOSE_MSG_WIN",
        "DATE_CHK",
        "GET_CNT",
        "GET_ITEM",
        "GET_SOCIAL_STAT_LEVEL",
        "GET_TIME_OF_DAY",
        "HELP_MSG",
        "MSG",
        "OPEN_MSG_WIN",
        "SEL",
        "SET_CNT",
        "SET_ITEM",
        "SET_MSG_VAR",
        "TITLED_HELP_MSG",
    }
)


def normalize_safety(mode: str | None, *, default: str = STANDARD) -> str:
    """Return the canonical safety mode name.

    Accepted public modes are beginner and standard. Common misspellings such as
    begginer and standart are accepted so small typos do not block beginners.
    The expert mode is kept for existing tests and internal conflict-check bypasses.
    """
    raw_mode = default if mode is None else str(mode).strip().lower()
    try:
        return SAFETY_ALIASES[raw_mode]
    except KeyError as exc:
        choices = ", ".join(sorted({BEGINNER, STANDARD, EXPERT, "begginer", "standart"}))
        raise P4GScriptError(f"Unknown safety mode: {mode}. Expected one of: {choices}") from exc


def is_beginner(mode: str | None) -> bool:
    """Return True when the provided mode resolves to beginner safety."""
    return normalize_safety(mode) == BEGINNER


def require_standard(mode: str | None, operation: str) -> None:
    """Reject an operation that should only be available in standard mode."""
    if is_beginner(mode):
        raise SafetyError(f"{operation} is not available in beginner safety mode")


def require_beginner_call_allowed(mode: str | None, function: str) -> None:
    """Reject direct native calls that beginner mode should not expose.

    Beginner users should normally call SDK helpers rather than raw native
    FlowScript functions. Standard mode keeps direct native calls available for
    advanced mod code.
    """
    if is_beginner(mode) and function not in BEGINNER_ALLOWED_CALLS:
        raise SafetyError(
            f"{function}(...) is a raw FlowScript call and is not available in beginner safety mode"
        )
