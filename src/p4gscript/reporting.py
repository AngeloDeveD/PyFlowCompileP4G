from __future__ import annotations

from collections import defaultdict
from typing import Iterable, TYPE_CHECKING

from .analyzer import (
    BitUsage,
    CountUsage,
    EventCallUsage,
    MessageCallUsage,
    MessageVarUsage,
    ProcedureUsage,
    TransitionCallUsage,
)

if TYPE_CHECKING:
    from .analyzer import WorkspaceAnalyzer


def render_procedure_report(analyzer: "WorkspaceAnalyzer", usage: ProcedureUsage) -> str:
    span = usage.span
    lines = [
        "Procedure Report",
        "================",
        f"File: {span.file}",
        f"Procedure: {span.name}",
        f"Index: {span.procedure_index}",
        f"Return: {span.return_type}",
        f"Lines: {span.start_line}-{span.end_line}",
        "",
    ]

    lines.extend(_message_section(analyzer, usage))
    lines.extend(_selection_section(analyzer, usage))
    lines.extend(_bit_section(usage.bits))
    lines.extend(_count_section(usage.counts))
    lines.extend(_event_section(usage.event_calls))
    lines.extend(_transition_section("Field Calls", usage.field_calls))
    lines.extend(_transition_section("Dungeon Calls", usage.dungeon_calls))
    lines.extend(_transition_section("Battle Calls", usage.battle_calls))
    lines.extend(_msg_var_section(usage.msg_vars))

    return "\n".join(lines).rstrip() + "\n"


def _message_section(analyzer: "WorkspaceAnalyzer", usage: ProcedureUsage) -> list[str]:
    return _message_like_section(analyzer, usage.span.file, "Message Calls", usage.message_calls)


def _selection_section(analyzer: "WorkspaceAnalyzer", usage: ProcedureUsage) -> list[str]:
    return _message_like_section(analyzer, usage.span.file, "Selection Calls", usage.selection_calls)


def _message_like_section(
    analyzer: "WorkspaceAnalyzer", flow_file: str, title: str, calls: list[MessageCallUsage]
) -> list[str]:
    lines = [f"{title}: {len(calls)}"]
    if not calls:
        return lines + [""]

    for name, grouped in _group_by_name(calls):
        first = grouped[0]
        call_count = len(grouped)
        line_text = _line_summary(call.line for call in grouped)
        if name is None:
            lines.append(f"  - dynamic expression `{first.expression}` x{call_count} at {line_text}")
            continue

        message_id = analyzer.message_id_for_flow(flow_file, name)
        id_text = f"id={message_id.value}" if message_id else "id=?"
        lines.append(f"  - {name} ({id_text}) x{call_count} at {line_text}")
    return lines + [""]


def _bit_section(bits: list[BitUsage]) -> list[str]:
    lines = [f"Bit Usages: {len(bits)}"]
    for key, grouped in _group_by(bits, lambda item: (item.function, item.bit_id, item.expression)):
        function, bit_id, expression = key
        id_text = f"id={bit_id}" if bit_id is not None else f"expr={expression}"
        lines.append(f"  - {function} {id_text} x{len(grouped)} at {_line_summary(item.line for item in grouped)}")
    return lines + [""]


def _count_section(counts: list[CountUsage]) -> list[str]:
    lines = [f"Count Usages: {len(counts)}"]
    for key, grouped in _group_by(counts, lambda item: (item.function, item.count_id, item.expression)):
        function, count_id, expression = key
        id_text = f"id={count_id}" if count_id is not None else f"expr={expression}"
        lines.append(f"  - {function} {id_text} x{len(grouped)} at {_line_summary(item.line for item in grouped)}")
    return lines + [""]


def _event_section(events: list[EventCallUsage]) -> list[str]:
    lines = [f"Event Calls: {len(events)}"]
    for args, grouped in _group_by(events, lambda item: item.args):
        lines.append(f"  - CALL_EVENT({', '.join(args)}) x{len(grouped)} at {_line_summary(item.line for item in grouped)}")
    return lines + [""]


def _transition_section(title: str, transitions: list[TransitionCallUsage]) -> list[str]:
    lines = [f"{title}: {len(transitions)}"]
    for key, grouped in _group_by(transitions, lambda item: (item.function, item.args)):
        function, args = key
        lines.append(f"  - {function}({', '.join(args)}) x{len(grouped)} at {_line_summary(item.line for item in grouped)}")
    return lines + [""]


def _msg_var_section(usages: list[MessageVarUsage]) -> list[str]:
    lines = [f"Message Var Usages: {len(usages)}"]
    for key, grouped in _group_by(usages, lambda item: item.args):
        lines.append(f"  - SET_MSG_VAR({', '.join(key)}) x{len(grouped)} at {_line_summary(item.line for item in grouped)}")
    return lines + [""]


def _group_by_name(calls: list[MessageCallUsage]) -> list[tuple[str | None, list[MessageCallUsage]]]:
    return _group_by(calls, lambda item: item.name)


def _group_by(items: Iterable, key_func) -> list[tuple[object, list]]:
    grouped = defaultdict(list)
    for item in items:
        grouped[key_func(item)].append(item)
    return sorted(grouped.items(), key=lambda pair: str(pair[0]))


def _line_summary(lines: Iterable[int], *, limit: int = 5) -> str:
    values = sorted(set(lines))
    shown = ", ".join(str(value) for value in values[:limit])
    if len(values) > limit:
        shown += ", ..."
    return f"line {shown}" if len(values) == 1 else f"lines {shown}"

