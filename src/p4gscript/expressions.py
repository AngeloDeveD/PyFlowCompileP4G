from __future__ import annotations

import re
from enum import IntEnum
from typing import Any

from .ids import BitId, EventId, FieldId


class Expr:
    """Base object for generated FlowScript expressions.

    Expr objects are not executed by Python. They describe code that will be
    written into the generated .flow file later. For example,
    bitChk(done) == 0 creates an expression that renders as
    BIT_CHK(done) == 0 inside proc.if_(...).
    """

    beginner_safe = True

    def render_flow(self) -> str:
        """Render this expression as FlowScript source code."""
        raise NotImplementedError

    def render_condition(self) -> str:
        """Render this expression for use inside a FlowScript condition."""
        return self.render_flow()

    def native_functions(self) -> tuple[str, ...]:
        """Return native FlowScript functions used by this expression.

        Beginner safety uses this list to reject advanced native calls when a
        safer SDK helper should be used instead.
        """
        return ()

    def __str__(self) -> str:
        return self.render_flow()

    def __bool__(self) -> bool:
        """Prevent accidental use in Python if statements.

        A P4GScript expression must be passed to proc.if_(...) or proc.when(...).
        Using it in a normal Python if would execute the condition while building
        the mod instead of generating a FlowScript condition for the game.
        """
        raise TypeError("P4GScript expressions must be passed to proc.if_(...) or proc.when(...).")

    def __eq__(self, other: object) -> "Expr":  # type: ignore[override]
        """Generate a FlowScript equality comparison."""
        return BinaryExpr(self, "==", value_expr(other))

    def __ne__(self, other: object) -> "Expr":  # type: ignore[override]
        """Generate a FlowScript inequality comparison."""
        return BinaryExpr(self, "!=", value_expr(other))

    def __lt__(self, other: Any) -> "Expr":
        """Generate a FlowScript less-than comparison."""
        return BinaryExpr(self, "<", value_expr(other))

    def __le__(self, other: Any) -> "Expr":
        """Generate a FlowScript less-or-equal comparison."""
        return BinaryExpr(self, "<=", value_expr(other))

    def __gt__(self, other: Any) -> "Expr":
        """Generate a FlowScript greater-than comparison."""
        return BinaryExpr(self, ">", value_expr(other))

    def __ge__(self, other: Any) -> "Expr":
        """Generate a FlowScript greater-or-equal comparison."""
        return BinaryExpr(self, ">=", value_expr(other))

    def __and__(self, other: Any) -> "Expr":
        """Generate a FlowScript logical AND expression.

        Python does not allow overriding the 'and' keyword, so beginner code
        should combine expressions with '&'. Always wrap comparisons in
        parentheses: (bitChk(done) == 0) & (timeOfDay() == TimeOfDay.EVENING).
        """
        return BinaryExpr(self, "&&", value_expr(other))

    def __or__(self, other: Any) -> "Expr":
        """Generate a FlowScript logical OR expression.

        Python does not allow overriding the 'or' keyword, so beginner code
        should combine expressions with '|'.
        """
        return BinaryExpr(self, "||", value_expr(other))

    def __invert__(self) -> "Expr":
        """Generate a FlowScript logical NOT expression using the '~' operator."""
        return UnaryExpr("!", self)


class ValueExpr(Expr):
    """Wrap a plain Python value so it can participate in expression rendering."""

    def __init__(self, value: Any):
        self.value = value

    def render_flow(self) -> str:
        return render_value(self.value)

    def native_functions(self) -> tuple[str, ...]:
        if isinstance(self.value, Expr):
            return self.value.native_functions()
        return ()


class RawExpr(Expr):
    """Advanced raw FlowScript expression.

    rawExpr(...) is intentionally blocked in beginner mode. It exists for
    standard mode when the SDK does not yet provide a typed helper for some
    native game function or rare expression.
    """

    beginner_safe = False

    def __init__(self, code: str):
        self.code = code

    def render_flow(self) -> str:
        return self.code


class IdentifierExpr(Expr):
    """Beginner-safe reference to a local FlowScript variable.

    Use var("choice") when a previous statement created a FlowScript variable,
    for example proc.sel("choice", selection). The name is validated so users
    cannot smuggle a full raw condition through this helper.
    """

    def __init__(self, name: str):
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None:
            raise ValueError(f"Unsafe FlowScript identifier: {name}")
        self.name = name

    def render_flow(self) -> str:
        return self.name


class UnaryExpr(Expr):
    """FlowScript unary expression such as !(BIT_CHK(flag) == 1)."""

    def __init__(self, operator: str, value: Expr):
        self.operator = operator
        self.value = value

    def render_flow(self) -> str:
        return f"{self.operator}({self.value.render_flow()})"

    def native_functions(self) -> tuple[str, ...]:
        return self.value.native_functions()


class BinaryExpr(Expr):
    """FlowScript binary expression such as BIT_CHK(flag) == 0."""

    def __init__(self, left: Expr, operator: str, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    def render_flow(self) -> str:
        return f"{self.left.render_flow()} {self.operator} {self.right.render_flow()}"

    def native_functions(self) -> tuple[str, ...]:
        return self.left.native_functions() + self.right.native_functions()


class CallExpr(Expr):
    """FlowScript native function call used as an expression or statement."""

    def __init__(self, function: str, *args: Any):
        self.function = function
        self.args = args

    def render_flow(self) -> str:
        """Render the call without a trailing semicolon."""
        rendered = ", ".join(render_value(arg) for arg in self.args)
        return f"{self.function}({rendered})"

    def render_statement(self) -> str:
        """Render the call as a complete FlowScript statement."""
        return f"{self.render_flow()};"

    def native_functions(self) -> tuple[str, ...]:
        nested: list[str] = [self.function]
        for arg in self.args:
            if isinstance(arg, Expr):
                nested.extend(arg.native_functions())
        return tuple(nested)


def render_value(value: Any) -> str:
    """Render a Python value as a FlowScript argument or expression part.

    Message and Selection objects render to their generated names, BitId renders
    to its constant name when available, and enum values render as their integer
    values because FlowScript expects numeric constants in these places.
    """
    if isinstance(value, Expr):
        return value.render_flow()
    if hasattr(value, "render_flow"):
        return value.render_flow()
    if hasattr(value, "name") and value.__class__.__name__ in {"Message", "Selection"}:
        return value.name
    if isinstance(value, BitId):
        return value.render()
    if isinstance(value, IntEnum):
        return str(int(value))
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def value_expr(value: Any) -> Expr:
    """Convert a plain Python value into an Expr when building comparisons."""
    if isinstance(value, Expr):
        return value
    return ValueExpr(value)


def var(name: str) -> Expr:
    """Reference a local FlowScript variable in a beginner-safe way.

    Example:
        proc.sel("choice", selection)
        with proc.if_(var("choice") == 0):
            ...
    """
    return IdentifierExpr(name)


def rawExpr(code: str) -> Expr:
    """Create an advanced raw FlowScript expression.

    This is for standard mode only. Prefer typed helpers such as bitChk(...),
    checkTimeSpan(...), dateChk(...), and timeOfDay() whenever they exist.
    """
    return RawExpr(code)


def callExpr(function: str, *args: Any) -> CallExpr:
    """Create a raw native FlowScript function call expression.

    Beginner mode allows only the native functions listed as safe by the SDK.
    Standard mode can use this for rare or currently unsupported native calls.
    """
    return CallExpr(function, *args)


def bitChk(bit: BitId | int) -> CallExpr:
    """Generate BIT_CHK(bit), which reads whether a game bit is enabled.

    It is normally used in conditions: proc.if_(bitChk(done_bit) == 0).
    """
    return CallExpr("BIT_CHK", bit)


def dateChk(month: int, day: int) -> CallExpr:
    """Generate DATE_CHK(month, day), which checks the current in-game date."""
    return CallExpr("DATE_CHK", month, day)


def checkTimeSpan(start_month: int, start_day: int, end_month: int, end_day: int) -> CallExpr:
    """Generate CHECK_TIME_SPAN for an inclusive in-game calendar range.

    The arguments are dates, not clock time: checkTimeSpan(4, 1, 5, 6) means
    April 1 through May 6. Compare the result to 1 in a condition.
    """
    return CallExpr("CHECK_TIME_SPAN", start_month, start_day, end_month, end_day)


def getTimeOfDay() -> CallExpr:
    """Generate GET_TIME_OF_DAY(), which returns the current P4G day slot.

    Prefer comparing it with TimeOfDay constants, for example
    proc.if_(timeOfDay() == TimeOfDay.EVENING).
    """
    return CallExpr("GET_TIME_OF_DAY")


def timeOfDay() -> CallExpr:
    """Alias for getTimeOfDay() with a shorter beginner-friendly name."""
    return getTimeOfDay()


def getCnt(index: int) -> CallExpr:
    """Generate GET_CNT(index), which reads a game counter value."""
    return CallExpr("GET_CNT", index)


def getItem(item_id: int) -> CallExpr:
    """Generate GET_ITEM(item_id), which reads the current amount of one item."""
    return CallExpr("GET_ITEM", item_id)


def socialStatLevel(stat: Any) -> CallExpr:
    """Generate GET_SOCIAL_STAT_LEVEL(stat), returning a social stat level.

    P4G social stat levels are 1..5. Pass a SocialStat constant, for example
    socialStatLevel(SocialStat.COURAGE) >= 3.
    """
    return CallExpr("GET_SOCIAL_STAT_LEVEL", stat)


def bitOn(bit: BitId | int) -> CallExpr:
    """Generate BIT_ON(bit), which enables a game bit."""
    return CallExpr("BIT_ON", bit)


def bitOff(bit: BitId | int) -> CallExpr:
    """Generate BIT_OFF(bit), which disables a game bit."""
    return CallExpr("BIT_OFF", bit)


def setCnt(index: int, value: int) -> CallExpr:
    """Generate SET_CNT(index, value), which writes a game counter value."""
    return CallExpr("SET_CNT", index, value)


def setItem(item_id: int, amount: int) -> CallExpr:
    """Generate SET_ITEM(item_id, amount), which changes an inventory count."""
    return CallExpr("SET_ITEM", item_id, amount)


def setMsgVar(index: int, value: Any, digits: int = 0) -> CallExpr:
    """Generate SET_MSG_VAR(index, value, digits) for message substitutions."""
    return CallExpr("SET_MSG_VAR", index, value, digits)


def addYen(amount: int) -> CallExpr:
    """Generate ADD_YEN(amount), which gives the player yen."""
    return CallExpr("ADD_YEN", amount)


def openMsg() -> CallExpr:
    """Generate OPEN_MSG_WIN(), which opens the message window."""
    return CallExpr("OPEN_MSG_WIN")


def closeMsg() -> CallExpr:
    """Generate CLOSE_MSG_WIN(), which closes the message window."""
    return CallExpr("CLOSE_MSG_WIN")


def msg(message: Any) -> CallExpr:
    """Generate MSG(message), which displays a MessageScript message block."""
    return CallExpr("MSG", message)


def helpMsg(message: Any) -> CallExpr:
    """Generate HELP_MSG(message), which displays a help-style message."""
    return CallExpr("HELP_MSG", message)


def titledHelpMsg(message: Any, title_id: Any) -> CallExpr:
    """Generate TITLED_HELP_MSG(message, title_id) for titled help popups."""
    return CallExpr("TITLED_HELP_MSG", message, title_id)


def callEvent(event: EventId | int, minor: int | None = None, sub: int = 0) -> CallExpr:
    """Generate CALL_EVENT(...), which starts an event script.

    Pass either EventId(major, minor, sub) or raw numeric parts as
    callEvent(major, minor, sub=0).
    """
    if isinstance(event, EventId):
        return CallExpr("CALL_EVENT", *event.args())
    if minor is None:
        raise TypeError("callEvent(major, minor, sub=0) requires minor")
    return CallExpr("CALL_EVENT", event, minor, sub)


def callField(
    field: FieldId | int,
    minor: int | None = None,
    location: int = 0,
    weather: int = 0,
    *,
    safe: bool = False,
) -> CallExpr:
    """Generate CALL_FIELD or CALL_FIELD_SAFE, which transfers to a field script.

    Pass either FieldId(major, minor, location, weather) or numeric parts as
    callField(major, minor, location=0, weather=0). Use safe=True to emit
    CALL_FIELD_SAFE instead of CALL_FIELD.
    """
    if isinstance(field, FieldId):
        return CallExpr("CALL_FIELD_SAFE" if safe else "CALL_FIELD", *field.args())
    if minor is None:
        raise TypeError("callField(major, minor, location=0, weather=0) requires minor")
    return CallExpr("CALL_FIELD_SAFE" if safe else "CALL_FIELD", field, minor, location, weather)
