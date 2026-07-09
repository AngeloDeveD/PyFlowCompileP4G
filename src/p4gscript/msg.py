from __future__ import annotations

import re

from dataclasses import dataclass, field
from typing import Any, Iterable

from .ids import Bustup, VoiceCue

# P4G dialogue boxes are treated conservatively as 40 visible characters per
# line and 3 lines per page. If auto-wrap produces more than 3 visual lines,
# MessageLine.render() emits a new [s]...[w][e] page for the remaining text.
# Dynamic runtime values such as [fName], [lName], and [var N] are counted as
# 8 visible characters because the game name-entry fields are limited and the
# final value is only known when the message is displayed.
DEFAULT_WRAP_WIDTH = 40
DEFAULT_MAX_LINES = 3
DYNAMIC_TEXT_WIDTH = 8


def resolve_bustup(value: Any) -> Bustup | None:
    """Return a Bustup from either a raw Bustup or a character-like object.

    Objects such as Character.YOSUKE expose default_bustup so user code can pass
    the character itself instead of repeating raw [bup ...] ids.
    """
    if value is None:
        return None
    if isinstance(value, Bustup):
        return value
    default_bustup = getattr(value, "default_bustup", None)
    if isinstance(default_bustup, Bustup):
        return default_bustup
    if default_bustup is None:
        return None
    raise TypeError(f"Unsupported bustup value: {value!r}")


_SAFE_INLINE_TAG_RE = re.compile(r"\[(?:fName|lName|var\s+\d+|n)\]")
_LINE_BREAK_TAG_RE = re.compile(r"\[n\]")
_WHITESPACE_RE = re.compile(r"\s+|\S+")


def _escape_literal_text(text: str) -> str:
    """Escape visible text and convert Python line breaks to [n]."""
    escaped = text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    return escaped.replace("\r\n", "[n]").replace("\r", "[n]").replace("\n", "[n]")


def escape_text(text: str) -> str:
    """Escape normal dialogue text while keeping SDK-approved inline tags.

    Helpers such as first_name() and line_break() return real MessageScript tags.
    Those tags must reach the compiler unchanged, but ordinary brackets must
    still be escaped because fan-translated Russian text can legitimately use
    ASCII [ and ] as visible letters. Keeping only a small allow-list gives the
    beginner API the expected behavior without turning every bracketed string
    into raw MessageScript.
    """
    result: list[str] = []
    cursor = 0
    for match in _SAFE_INLINE_TAG_RE.finditer(text):
        result.append(_escape_literal_text(text[cursor:match.start()]))
        result.append(match.group(0))
        cursor = match.end()
    result.append(_escape_literal_text(text[cursor:]))
    return "".join(result)


def _tag_width(tag: str) -> int:
    """Return visible width for safe inline tags used inside wrapped text."""
    if tag in {"[fName]", "[lName]"}:
        return DYNAMIC_TEXT_WIDTH
    if tag.startswith("[var "):
        return DYNAMIC_TEXT_WIDTH
    return 0


def _iter_visible_units(text: str):
    """Yield rendered text units with their visible width.

    Escaped brackets such as \\[ are one visible character. Safe inline tags are
    kept as one unit so auto-wrap never splits [fName] or [var 0] in half.
    """
    index = 0
    while index < len(text):
        if text.startswith((r"\[", r"\]", r"\\"), index):
            yield text[index:index + 2], 1
            index += 2
            continue

        tag_match = _SAFE_INLINE_TAG_RE.match(text, index)
        if tag_match:
            tag = tag_match.group(0)
            yield tag, _tag_width(tag)
            index = tag_match.end()
            continue

        yield text[index], 1
        index += 1


def _visible_width(text: str) -> int:
    """Measure the visible width of already-escaped MessageScript text."""
    return sum(width for _, width in _iter_visible_units(text))


def _split_long_token(token: str, width: int) -> list[str]:
    """Split a token that cannot fit on one line without breaking tags."""
    if width <= 0 or _visible_width(token) <= width:
        return [token]

    chunks: list[str] = []
    current: list[str] = []
    current_width = 0
    for raw, unit_width in _iter_visible_units(token):
        if current and current_width + unit_width > width:
            chunks.append("".join(current))
            current = []
            current_width = 0
        current.append(raw)
        current_width += unit_width
    if current:
        chunks.append("".join(current))
    return chunks or [token]


def _wrap_segment(segment: str, width: int) -> list[str]:
    """Wrap one visual paragraph that does not contain explicit [n] breaks."""
    if segment == "" or width <= 0:
        return [segment]

    lines: list[str] = []
    line_parts: list[str] = []
    line_width = 0
    pending_space = False

    for token in _WHITESPACE_RE.findall(segment):
        if token.isspace():
            if line_parts:
                pending_space = True
            continue

        chunks = _split_long_token(token, width)
        for index, chunk in enumerate(chunks):
            chunk_width = _visible_width(chunk)
            needs_space = pending_space and bool(line_parts)
            added_width = chunk_width + (1 if needs_space else 0)

            if line_parts and line_width + added_width > width:
                lines.append("".join(line_parts).rstrip())
                line_parts = []
                line_width = 0
                needs_space = False

            if needs_space:
                line_parts.append(" ")
                line_width += 1

            line_parts.append(chunk)
            line_width += chunk_width
            pending_space = False

            if index < len(chunks) - 1:
                lines.append("".join(line_parts).rstrip())
                line_parts = []
                line_width = 0

    if line_parts:
        lines.append("".join(line_parts).rstrip())
    return lines or [""]


def wrap_message_text(text: str, width: int = DEFAULT_WRAP_WIDTH, max_lines: int = DEFAULT_MAX_LINES) -> list[list[str]]:
    """Wrap escaped MessageScript text into pages of visual lines.

    width is measured in visible characters. [fName], [lName], and [var N] are
    treated as DYNAMIC_TEXT_WIDTH characters because their real value is only
    known when the game displays the message.
    """
    visual_lines: list[str] = []
    cursor = 0
    for match in _LINE_BREAK_TAG_RE.finditer(text):
        visual_lines.extend(_wrap_segment(text[cursor:match.start()], width))
        cursor = match.end()
    visual_lines.extend(_wrap_segment(text[cursor:], width))

    page_size = max(1, max_lines)
    return [visual_lines[index:index + page_size] for index in range(0, len(visual_lines), page_size)] or [[""]]


def msg_var(index: int) -> str:
    """Return a MessageScript variable tag such as [var 0]."""
    return f"[var {index}]"


def first_name() -> str:
    """Return the MessageScript tag for the protagonist first name."""
    return "[fName]"


def last_name() -> str:
    """Return the MessageScript tag for the protagonist last name."""
    return "[lName]"


def line_break() -> str:
    """Return the MessageScript tag for a line break inside one dialogue box."""
    return "[n]"


def new_line() -> str:
    """Alias for line_break(), kept for readable beginner scripts."""
    return line_break()


@dataclass
class MessageLine:
    """One rendered line inside a MessageScript [msg ...] block."""

    text: str
    wait: bool = True
    newline: bool = True
    bustup: Bustup | None = None
    voice: VoiceCue | None = None
    raw_prefix: list[str] = field(default_factory=list)
    escape: bool = True
    auto_wrap: bool = True
    wrap_width: int = DEFAULT_WRAP_WIDTH
    max_lines: int = DEFAULT_MAX_LINES

    def render(self) -> str:
        """Render this line with standard P4G message tags."""
        text = escape_text(self.text) if self.escape else self.text
        pages = wrap_message_text(text, self.wrap_width, self.max_lines) if self.auto_wrap and self.escape else [[text]]
        rendered_pages: list[str] = []
        for index, page in enumerate(pages):
            rendered_pages.append(self._render_page("[n]".join(page), include_voice=index == 0))
        return "\n".join(rendered_pages)

    def _render_page(self, text: str, *, include_voice: bool) -> str:
        parts = ["[s]"]
        parts.extend(self.raw_prefix)
        if include_voice and self.voice is not None:
            parts.append(self.voice.render())
        if self.bustup is not None:
            parts.append(self.bustup.render())
        parts.append(text)
        if self.newline:
            parts.append("[n]")
        if self.wait:
            parts.append("[w]")
        parts.append("[e]")
        return "".join(parts)


@dataclass
class Message:
    """MessageScript dialogue block rendered as [msg NAME [Speaker]]."""

    name: str
    speaker: str | None = None
    default_bustup: Bustup | None = None
    lines: list[MessageLine] = field(default_factory=list)

    def line(
        self,
        text: str,
        *,
        wait: bool = True,
        newline: bool = True,
        bustup: Any | None = None,
        voice: VoiceCue | None = None,
        raw_prefix: Iterable[str] = (),
        escape: bool = True,
        auto_wrap: bool = True,
        wrap_width: int = DEFAULT_WRAP_WIDTH,
        max_lines: int = DEFAULT_MAX_LINES,
    ) -> "Message":
        """Add one dialogue line to this message.

        wait=True adds [w], newline=True adds a final [n]. Python newlines in
        text are converted to in-box [n] breaks, and auto_wrap=True wraps long
        text to wrap_width visible characters with at most max_lines per page.
        Pass Bustup or VoiceCue to insert portrait or voice tags before the text.
        Set escape=False only when text intentionally contains raw MessageScript
        tags; raw text is not auto-wrapped.
        """
        self.lines.append(
            MessageLine(
                text=text,
                wait=wait,
                newline=newline,
                bustup=resolve_bustup(bustup) if bustup is not None else self.default_bustup,
                voice=voice,
                raw_prefix=list(raw_prefix),
                escape=escape,
                auto_wrap=auto_wrap,
                wrap_width=wrap_width,
                max_lines=max_lines,
            )
        )
        return self

    def raw_line(self, text: str) -> "Message":
        """Add a raw MessageScript line without automatic [n], [w], or escaping."""
        self.lines.append(MessageLine(text=text, wait=False, newline=False, escape=False, auto_wrap=False))
        return self

    def render(self) -> str:
        """Render this complete message block."""
        speaker = f" [{self.speaker}]" if self.speaker else ""
        body = "\n".join(line.render() for line in self.lines)
        return f"[msg {self.name}{speaker}]\n{body}".rstrip()


@dataclass
class Selection:
    """MessageScript selection block rendered as [sel NAME pattern]."""

    name: str
    pattern: str = "top"
    options: list[str] = field(default_factory=list)

    def option(self, text: str) -> "Selection":
        """Add one selectable option to this selection block."""
        self.options.append(text)
        return self

    def render(self) -> str:
        """Render this complete selection block."""
        lines = [f"[sel {self.name} {self.pattern}]"]
        for option in self.options:
            lines.append(f"[s]{escape_text(option)}[e]")
        return "\n".join(lines)


@dataclass
class MessageDocument:
    """Complete .msg document containing messages and selections."""

    messages: list[Message] = field(default_factory=list)
    selections: list[Selection] = field(default_factory=list)

    def render(self) -> str:
        """Render the full .msg file text."""
        blocks: list[str] = []
        blocks.extend(message.render() for message in self.messages)
        blocks.extend(selection.render() for selection in self.selections)
        return "\n\n".join(blocks).rstrip() + "\n"