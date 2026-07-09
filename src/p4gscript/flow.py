from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any

from .conditions import Date, render_condition
from .exceptions import RenderError
from .expressions import bitChk, checkTimeSpan, render_value, timeOfDay, var
from .ids import BitId, EventId, FieldId
from .safety import require_beginner_call_allowed, require_standard


def render_arg(value: Any) -> str:
    """Render one Python value as a FlowScript call argument."""
    return render_value(value)


class CodeBlock(AbstractContextManager["CodeBlock"]):
    """Context manager that writes a braced FlowScript block.

    Users normally do not create CodeBlock directly. It is returned by helpers
    such as proc.if_(...) and then used through Python's with statement.
    """

    def __init__(self, procedure: "Procedure", header: str):
        self.procedure = procedure
        self.header = header

    def __enter__(self) -> "CodeBlock":
        self.procedure.line(f"{self.header}")
        self.procedure.line("{")
        self.procedure.indent += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.procedure.indent -= 1
        self.procedure.line("}")
        return False


class OnceBlock(CodeBlock):
    """Context manager for one-time blocks guarded by a mod bit.

    The block opens as a normal `if (...) {` statement, but when the `with`
    body exits successfully it automatically writes `BIT_ON(done_bit);` before
    the closing brace. This keeps a common modding pattern concise and harder to
    forget.
    """

    def __init__(self, procedure: "Procedure", header: str, done_bit: BitId | int):
        super().__init__(procedure, header)
        self.done_bit = done_bit

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is None:
            self.procedure.bit_on(self.done_bit)
        self.procedure.indent -= 1
        self.procedure.line("}")
        return False


@dataclass
class Procedure:
    """Builder for one FlowScript procedure.

    A Procedure collects statements and renders them as a single .flow function.
    Beginner users should prefer typed helpers such as say(...), if_(Expr),
    setBit(...), call_event(...), and call_field(...). Standard users can also
    use raw(...), call(...), and string conditions for advanced native code.
    """

    name: str
    return_type: str = "void"
    params: str = ""
    project: Any | None = None
    statements: list[str] = field(default_factory=list)
    indent: int = 1
    auto_return: bool = True

    def line(self, code: str = "") -> "Procedure":
        """Append one already-rendered FlowScript line at the current indent.

        This is a low-level helper used by the SDK itself. User code should
        usually call higher-level methods because line(...) does not validate
        syntax or safety.
        """
        self.statements.append(("    " * self.indent) + code if code else "")
        return self

    def raw(self, code: str) -> "Procedure":
        """Append raw FlowScript source code.

        This is standard-mode API. It is blocked in beginner mode because raw
        code bypasses the SDK's helpers and makes mistakes harder to diagnose.
        Use it only when the SDK does not yet expose the native behavior you need.
        """
        require_standard(self._safety_mode(), "Procedure.raw(...)")
        for line in code.splitlines():
            self.line(line)
        return self

    def const_int(self, name: str, value: int) -> "Procedure":
        """Write a local FlowScript const int declaration inside this procedure."""
        self.line(f"const int {name} = {value};")
        return self

    def call(self, function: str, *args: Any) -> "Procedure":
        """Emit a direct native FlowScript function call.

        In beginner mode only SDK-approved common calls are allowed. In standard
        mode this can call rare native functions directly, for example
        proc.call("SAVE_ASK", 3).
        """
        require_beginner_call_allowed(self._safety_mode(), function)
        return self._emit_call(function, *args)

    def assign_call(self, variable: str, function: str, *args: Any, declare: str | None = "int") -> "Procedure":
        """Emit a native call and store the result in a FlowScript variable.

        Example: proc.assign_call("value", "GET_CNT", 10) renders
        int value = GET_CNT(10);. Pass declare=None when the variable already
        exists and should not be redeclared.
        """
        require_beginner_call_allowed(self._safety_mode(), function)
        return self._emit_assign_call(variable, function, *args, declare=declare)

    def emit(self, call: Any) -> "Procedure":
        """Emit a CallExpr returned by expression helpers as a statement.

        Example: proc.emit(bitOn(done)) renders BIT_ON(done);. Passing a plain
        string is treated as raw FlowScript and is therefore blocked in beginner
        mode.
        """
        if isinstance(call, str) or not hasattr(call, "render_statement"):
            require_standard(self._safety_mode(), "Raw FlowScript statements")
            self.line(str(call))
            return self
        if getattr(call, "beginner_safe", True) is False:
            require_standard(self._safety_mode(), "Raw FlowScript expressions")
        for function in getattr(call, "native_functions", lambda: ())():
            require_beginner_call_allowed(self._safety_mode(), function)
        self.line(call.render_statement())
        return self

    def open_msg(self) -> "Procedure":
        """Open the P4G message window with OPEN_MSG_WIN()."""
        return self._emit_call("OPEN_MSG_WIN")

    def close_msg(self) -> "Procedure":
        """Close the P4G message window with CLOSE_MSG_WIN()."""
        return self._emit_call("CLOSE_MSG_WIN")

    def msg(self, message: Any) -> "Procedure":
        """Display a MessageScript message or selection using MSG(...)."""
        return self._emit_call("MSG", message)

    def help_msg(self, message: Any) -> "Procedure":
        """Display a help-style message using HELP_MSG(...)."""
        return self._emit_call("HELP_MSG", message)

    def titled_help_msg(self, message: Any, title_id: Any) -> "Procedure":
        """Display a titled help message using TITLED_HELP_MSG(...)."""
        return self._emit_call("TITLED_HELP_MSG", message, title_id)

    def help(
        self,
        message_or_text: Any,
        *,
        name: str | None = None,
        wait: bool = True,
        newline: bool = True,
        raw_prefix=(),
        escape: bool = True,
        auto_wrap: bool = True,
        wrap_width: int = 40,
        max_lines: int = 3,
    ) -> "Procedure":
        """Display a help-style message with HELP_MSG(...).

        Pass an existing Message object, or pass plain text and the SDK will
        create a MessageScript block automatically. Unlike say(...), this helper
        does not open or close the normal dialogue window because HELP_MSG uses
        the game's help-message presentation.
        """
        if isinstance(message_or_text, str):
            if self.project is None:
                raise RenderError("Procedure.help(text) requires a project-bound procedure")
            message = self.project.message(name or self._next_message_name())
            message.line(
                message_or_text,
                wait=wait,
                newline=newline,
                raw_prefix=raw_prefix,
                escape=escape,
                auto_wrap=auto_wrap,
                wrap_width=wrap_width,
                max_lines=max_lines,
            )
        else:
            message = message_or_text
        return self.help_msg(message)

    def sel(self, variable: str, selection: Any, *, declare: str | None = "int") -> "Procedure":
        """Display a selection and store the selected option index.

        The generated variable can be used later with var(variable). Option
        indexes start from 0, matching the original FlowScript behavior.
        """
        return self._emit_assign_call(variable, "SEL", selection, declare=declare)

    def ask(
        self,
        variable: str,
        *options: str,
        name: str | None = None,
        pattern: str = "top",
        declare: str | None = "int",
    ) -> Any:
        """Create a selection block, render SEL(...), and return var(variable).

        This helper is meant for the common beginner pattern where a procedure
        needs a short menu without manually creating a Selection object first.

        Example:
            choice = proc.ask("choice", "Go out", "Stay home")
            with proc.if_(choice == 0):
                ...
        """
        if self.project is None:
            raise RenderError("Procedure.ask(...) requires a project-bound procedure")
        if not options:
            raise RenderError("Procedure.ask(...) requires at least one option")
        selection = self.project.selection(name or self._next_selection_name(), pattern=pattern)
        for option in options:
            selection.option(option)
        self.sel(variable, selection, declare=declare)
        return var(variable)

    def ask_yes_no(
        self,
        variable: str = "choice",
        *,
        yes: str = "Yes",
        no: str = "No",
        name: str | None = None,
        declare: str | None = "int",
    ) -> Any:
        """Create a simple two-option yes/no selection and return var(variable)."""
        return self.ask(variable, yes, no, name=name, pattern="top", declare=declare)

    def bit_on(self, bit: BitId | int) -> "Procedure":
        """Enable a bit with BIT_ON(bit) and register named BitId constants."""
        self._warn_unsafe_bit(bit)
        return self._emit_call("BIT_ON", bit)

    def bit_off(self, bit: BitId | int) -> "Procedure":
        """Disable a bit with BIT_OFF(bit) and register named BitId constants."""
        self._warn_unsafe_bit(bit)
        return self._emit_call("BIT_OFF", bit)

    def set_bit(self, bit: BitId | int) -> "Procedure":
        """Python-style alias for bit_on(...)."""
        return self.bit_on(bit)

    def clear_bit(self, bit: BitId | int) -> "Procedure":
        """Python-style alias for bit_off(...)."""
        return self.bit_off(bit)

    def setBit(self, bit: BitId | int) -> "Procedure":
        """Beginner-friendly alias for bit_on(...)."""
        return self.bit_on(bit)

    def clearBit(self, bit: BitId | int) -> "Procedure":
        """Beginner-friendly alias for bit_off(...)."""
        return self.bit_off(bit)

    def add_yen(self, amount: int) -> "Procedure":
        """Give the player yen with ADD_YEN(amount)."""
        return self._emit_call("ADD_YEN", amount)

    def addYen(self, amount: int) -> "Procedure":
        """Beginner-friendly alias for add_yen(...)."""
        return self.add_yen(amount)

    def set_item(self, item_id: int, amount: int) -> "Procedure":
        """Give or remove items with SET_ITEM(item_id, amount)."""
        return self._emit_call("SET_ITEM", item_id, amount)

    def setItem(self, item_id: int, amount: int) -> "Procedure":
        """Beginner-friendly alias for set_item(...)."""
        return self.set_item(item_id, amount)

    def get_item(self, variable: str, item_id: int, *, declare: str | None = "int") -> "Procedure":
        """Read GET_ITEM(item_id) into a FlowScript variable."""
        return self._emit_assign_call(variable, "GET_ITEM", item_id, declare=declare)

    def getItem(self, variable: str, item_id: int, *, declare: str | None = "int") -> "Procedure":
        """Beginner-friendly alias for get_item(...)."""
        return self.get_item(variable, item_id, declare=declare)

    def set_msg_var(self, index: int, value: Any, digits: int = 0) -> "Procedure":
        """Populate a MessageScript variable slot with SET_MSG_VAR(...)."""
        return self._emit_call("SET_MSG_VAR", index, value, digits)

    def setMsgVar(self, index: int, value: Any, digits: int = 0) -> "Procedure":
        """Beginner-friendly alias for set_msg_var(...)."""
        return self.set_msg_var(index, value, digits)

    def call_event(self, event: EventId) -> "Procedure":
        """Start an event script with CALL_EVENT(event.major, event.minor, event.sub)."""
        return self._emit_call("CALL_EVENT", *event.args())

    def call_field(self, field: FieldId, *, safe: bool = False) -> "Procedure":
        """Transfer to a field script with CALL_FIELD or CALL_FIELD_SAFE."""
        return self._emit_call("CALL_FIELD_SAFE" if safe else "CALL_FIELD", *field.args())

    def call_original(self) -> "Procedure":
        """Call the original procedure from inside a hook.

        For a hook named select_nanako_okaeri_hook this emits
        select_nanako_okaeri_unhooked();. Use it when a mod should add behavior
        before or after the original game code instead of fully replacing it.
        """
        if self.name.endswith("_hook"):
            return self._emit_call(f"{self.name[:-5]}_unhooked")
        if self.name.endswith("_softhook"):
            return self._emit_call(f"{self.name[:-9]}_unhooked")
        if self.name.endswith("_hookafter"):
            return self._emit_call(f"{self.name[:-10]}_unhooked")
        return self._emit_call(f"{self.name}_unhooked")

    def callOriginal(self) -> "Procedure":
        """Beginner-friendly alias for call_original()."""
        return self.call_original()

    def return_(self) -> "Procedure":
        """Emit return; and disable the automatic final return for this procedure."""
        self.line("return;")
        self.auto_return = False
        return self

    def if_(self, condition: Any) -> CodeBlock:
        """Create a FlowScript if block.

        Beginner mode accepts SDK expressions such as bitChk(done) == 0 and
        checkTimeSpan(4, 1, 5, 6) == 1. String conditions are standard-mode API
        because they bypass validation and are easier to mistype.
        """
        self._validate_condition(condition)
        return CodeBlock(self, f"if ({render_condition(condition)})")

    def when(self, condition: Any) -> CodeBlock:
        """Alias for if_(condition), kept for readable calendar-style checks."""
        return self.if_(condition)

    def when_bit_clear(self, bit: BitId | int) -> CodeBlock:
        """Create `if (BIT_CHK(bit) == 0)` for a common one-bit guard."""
        self._warn_unsafe_bit(bit)
        return self.if_(bitChk(bit) == 0)

    def when_bit_set(self, bit: BitId | int) -> CodeBlock:
        """Create `if (BIT_CHK(bit) == 1)` for a common one-bit guard."""
        self._warn_unsafe_bit(bit)
        return self.if_(bitChk(bit) == 1)

    def when_time(self, slot: Any) -> CodeBlock:
        """Create `if (GET_TIME_OF_DAY() == slot)` with a typed day-slot value."""
        return self.if_(timeOfDay() == slot)

    def during(self, start_month: int, start_day: int, end_month: int, end_day: int) -> CodeBlock:
        """Create `if (CHECK_TIME_SPAN(...) == 1)` for a date-range check.

        This exists because date-span checks are one of the most common patterns
        in P4G field and event mods, and writing them by hand repeatedly adds a
        lot of noise to beginner code.
        """
        return self.if_(checkTimeSpan(start_month, start_day, end_month, end_day) == 1)

    def once(self, done_bit: BitId | int, *, condition: Any | None = None) -> OnceBlock:
        """Create a one-time guarded block and set the bit automatically.

        Example:
            with proc.once(done, condition=checkTimeSpan(4, 1, 5, 6) == 1):
                proc.say(Speaker.NANAKO, "Hello once.")

        The rendered block checks `BIT_CHK(done_bit) == 0` and writes
        `BIT_ON(done_bit);` at the end of the block automatically.
        """
        self._warn_unsafe_bit(done_bit)
        guard = f"BIT_CHK({render_arg(done_bit)}) == 0"
        if condition is not None:
            self._validate_condition(condition)
            guard = f"{guard} && ({render_condition(condition)})"
        return OnceBlock(self, f"if ({guard})", done_bit)

    def say(
        self,
        speaker_or_message: Any,
        text: str | None = None,
        *,
        name: str | None = None,
        wait: bool = True,
        newline: bool = True,
        bustup: Any | None = None,
        voice: Any | None = None,
        raw_prefix=(),
        escape: bool = True,
        auto_wrap: bool = True,
        wrap_width: int = 40,
        max_lines: int = 3,
    ) -> "Procedure":
        """Display a short dialogue message with open/message/close calls.

        Pass either an existing Message object, or pass speaker and text:
        proc.say(Speaker.NANAKO, "Good morning!"). When speaker and text are
        provided, the SDK creates a MessageScript block, opens the message
        window, displays it, and closes the window.
        """
        if text is None:
            message = speaker_or_message
        else:
            if self.project is None:
                raise RenderError("Procedure.say(speaker, text) requires a project-bound procedure")
            message = self.project.message(name or self._next_message_name(), speaker=speaker_or_message)
            message.line(
                text,
                wait=wait,
                newline=newline,
                bustup=bustup,
                voice=voice,
                raw_prefix=raw_prefix,
                escape=escape,
                auto_wrap=auto_wrap,
                wrap_width=wrap_width,
                max_lines=max_lines,
            )
        self.open_msg()
        self.msg(message)
        self.close_msg()
        return self

    def if_date(self, month: int, day: int, *, done_bit: BitId | int | None = None) -> CodeBlock:
        """Create an if block for DATE_CHK(month, day) == 1.

        If done_bit is provided, the condition also checks that the bit is not
        already set. This is useful for one-time messages or events.
        """
        condition = Date(month, day).render_condition()
        if done_bit is not None:
            self._warn_unsafe_bit(done_bit)
            condition += f" && BIT_CHK({render_arg(done_bit)}) == 0"
        return CodeBlock(self, f"if ({condition})")

    def _emit_call(self, function: str, *args: Any) -> "Procedure":
        rendered = ", ".join(render_arg(arg) for arg in args)
        self.line(f"{function}({rendered});")
        return self

    def _emit_assign_call(self, variable: str, function: str, *args: Any, declare: str | None = "int") -> "Procedure":
        rendered = ", ".join(render_arg(arg) for arg in args)
        prefix = f"{declare} " if declare else ""
        self.line(f"{prefix}{variable} = {function}({rendered});")
        return self

    def _next_message_name(self) -> str:
        if self.project is None:
            return f"{self.name}_MSG_1"
        names = {message.name for message in self.project.messages}
        names.update(selection.name for selection in self.project.selections)
        names.update(procedure.name for procedure in self.project.procedures)
        index = len(self.project.messages) + 1
        while True:
            candidate = f"{self.name}_MSG_{index}"
            if candidate not in names:
                return candidate
            index += 1

    def _next_selection_name(self) -> str:
        if self.project is None:
            return f"{self.name}_SEL_1"
        names = {message.name for message in self.project.messages}
        names.update(selection.name for selection in self.project.selections)
        names.update(procedure.name for procedure in self.project.procedures)
        index = len(self.project.selections) + 1
        while True:
            candidate = f"{self.name}_SEL_{index}"
            if candidate not in names:
                return candidate
            index += 1

    def _safety_mode(self) -> str:
        return getattr(self.project, "safety", "standard")

    def _validate_condition(self, condition: Any) -> None:
        if isinstance(condition, str):
            require_standard(self._safety_mode(), "Raw string conditions")
        if getattr(condition, "beginner_safe", True) is False:
            require_standard(self._safety_mode(), "Raw FlowScript expressions")
        for function in getattr(condition, "native_functions", lambda: ())():
            require_beginner_call_allowed(self._safety_mode(), function)

    def _warn_unsafe_bit(self, bit: BitId | int) -> None:
        if isinstance(bit, BitId) and self.project is not None:
            self.project.register_bit(bit)
        if isinstance(bit, BitId) and not bit.safe and self.project is not None:
            label = bit.name or str(bit.value)
            reason = f": {bit.reason}" if bit.reason else ""
            self.project.warn(f"Unsafe bit {label}{reason}")

    def render(self) -> str:
        """Render this procedure as complete FlowScript source code."""
        header = f"{self.return_type} {self.name}({self.params})"
        lines = [header, "{"]
        lines.extend(self.statements)
        if self.auto_return and self.return_type == "void":
            lines.append("    return;")
        lines.append("}")
        return "\n".join(lines)


@dataclass
class FlowDocument:
    """Complete FlowScript document containing imports, constants, and procedures."""

    imports: list[str] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)
    procedures: list[Procedure] = field(default_factory=list)

    def render(self) -> str:
        """Render the full .flow file text."""
        chunks: list[str] = []
        if self.imports:
            chunks.append("\n".join(f'import("{path}");' for path in self.imports))
        if self.constants:
            chunks.append("\n".join(self.constants))
        chunks.extend(procedure.render() for procedure in self.procedures)
        return "\n\n".join(chunks).rstrip() + "\n"

