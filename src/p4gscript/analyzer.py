from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ProcedureRecord:
    file: str
    procedure_index: int
    return_type: str
    name: str


@dataclass(frozen=True)
class ProcedureSpan:
    file: str
    procedure_index: int
    return_type: str
    name: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class NativeCallSummary:
    function: str
    call_count: int
    file_count: int


@dataclass(frozen=True)
class MessageTagSummary:
    tag: str
    count: int


@dataclass(frozen=True)
class MessageIdRecord:
    file: str
    name: str
    value: int


@dataclass(frozen=True)
class ImportRecord:
    file: str
    line: int
    path: str


@dataclass(frozen=True)
class BitUsage:
    file: str
    line: int
    function: str
    expression: str
    bit_id: int | None


@dataclass(frozen=True)
class CountUsage:
    file: str
    line: int
    function: str
    expression: str
    count_id: int | None


@dataclass(frozen=True)
class EventCallUsage:
    file: str
    line: int
    args: tuple[str, ...]

    @property
    def major(self) -> str | None:
        return self.args[0] if len(self.args) > 0 else None

    @property
    def minor(self) -> str | None:
        return self.args[1] if len(self.args) > 1 else None

    @property
    def sub(self) -> str | None:
        return self.args[2] if len(self.args) > 2 else None


@dataclass(frozen=True)
class MessageCallUsage:
    file: str
    line: int
    function: str
    expression: str
    name: str | None

    @property
    def is_dynamic(self) -> bool:
        return self.name is None


@dataclass(frozen=True)
class MessageVarUsage:
    file: str
    line: int
    args: tuple[str, ...]

    @property
    def slot(self) -> int | None:
        return _try_eval_int(self.args[0]) if len(self.args) > 0 else None

    @property
    def value_expression(self) -> str | None:
        return self.args[1] if len(self.args) > 1 else None

    @property
    def type_expression(self) -> str | None:
        return self.args[2] if len(self.args) > 2 else None


@dataclass(frozen=True)
class TransitionCallUsage:
    file: str
    line: int
    function: str
    args: tuple[str, ...]

    @property
    def first_arg(self) -> str | None:
        return self.args[0] if self.args else None


@dataclass(frozen=True)
class ProcedureUsage:
    span: ProcedureSpan
    bits: list[BitUsage]
    counts: list[CountUsage]
    event_calls: list[EventCallUsage]
    message_calls: list[MessageCallUsage]
    selection_calls: list[MessageCallUsage]
    msg_vars: list[MessageVarUsage]
    field_calls: list[TransitionCallUsage]
    dungeon_calls: list[TransitionCallUsage]
    battle_calls: list[TransitionCallUsage]


@dataclass
class WorkspaceAnalyzer:
    root: Path
    procedures: list[ProcedureRecord] = field(default_factory=list)
    procedure_spans: list[ProcedureSpan] = field(default_factory=list)
    native_calls: list[NativeCallSummary] = field(default_factory=list)
    message_tags: list[MessageTagSummary] = field(default_factory=list)
    message_ids: list[MessageIdRecord] = field(default_factory=list)
    imports: list[ImportRecord] = field(default_factory=list)
    bits: list[BitUsage] = field(default_factory=list)
    counts: list[CountUsage] = field(default_factory=list)
    event_calls: list[EventCallUsage] = field(default_factory=list)
    message_calls: list[MessageCallUsage] = field(default_factory=list)
    selection_calls: list[MessageCallUsage] = field(default_factory=list)
    msg_vars: list[MessageVarUsage] = field(default_factory=list)
    field_calls: list[TransitionCallUsage] = field(default_factory=list)
    dungeon_calls: list[TransitionCallUsage] = field(default_factory=list)
    battle_calls: list[TransitionCallUsage] = field(default_factory=list)

    @classmethod
    def load(cls, root: str | Path) -> "WorkspaceAnalyzer":
        analyzer = cls(root=Path(root))
        analyzer.load_indexes()
        analyzer.scan_decompiled()
        return analyzer

    @property
    def decompiled_dir(self) -> Path:
        return self.root / "decompiled"

    @property
    def indexes_dir(self) -> Path:
        return self.root / "indexes"

    def load_indexes(self) -> None:
        self.procedures = [
            ProcedureRecord(
                file=row["file"],
                procedure_index=int(row["procedure_index"]),
                return_type=row["return_type"],
                name=row["name"],
            )
            for row in self._read_tsv("procedures.tsv")
        ]

        self.native_calls = [
            NativeCallSummary(
                function=row["function"],
                call_count=int(row["call_count"]),
                file_count=int(row["file_count"]),
            )
            for row in self._read_tsv("native_calls.tsv")
        ]

        self.message_tags = [
            MessageTagSummary(tag=row["tag"], count=int(row["count"]))
            for row in self._read_tsv("message_tags.tsv")
        ]

    def scan_decompiled(self) -> None:
        if not self.decompiled_dir.exists():
            return
        self.message_ids = list(self._scan_message_ids())
        self.procedure_spans = []
        self.imports = []
        self.bits = []
        self.counts = []
        self.event_calls = []
        self.message_calls = []
        self.selection_calls = []
        self.msg_vars = []
        self.field_calls = []
        self.dungeon_calls = []
        self.battle_calls = []

        for path in self.decompiled_dir.rglob("*.flow"):
            self._scan_flow_file(path)

    def procedures_named(self, name: str) -> list[ProcedureRecord]:
        return [record for record in self.procedures if record.name == name]

    def procedure_spans_named(self, name: str) -> list[ProcedureSpan]:
        return [span for span in self.procedure_spans if span.name == name]

    def procedure_at(self, file: str, line: int) -> ProcedureSpan | None:
        for span in self.procedure_spans:
            if _same_file(span.file, file) and span.start_line <= line <= span.end_line:
                return span
        return None

    def procedure_usages(self, file: str, procedure: str | int) -> list[ProcedureUsage]:
        spans = [
            span
            for span in self.procedure_spans
            if _same_file(span.file, file)
            and ((isinstance(procedure, str) and span.name == procedure) or span.procedure_index == procedure)
        ]
        return [self.usages_for_span(span) for span in spans]

    def usages_for_span(self, span: ProcedureSpan) -> ProcedureUsage:
        return ProcedureUsage(
            span=span,
            bits=_filter_usage(self.bits, span),
            counts=_filter_usage(self.counts, span),
            event_calls=_filter_usage(self.event_calls, span),
            message_calls=_filter_usage(self.message_calls, span),
            selection_calls=_filter_usage(self.selection_calls, span),
            msg_vars=_filter_usage(self.msg_vars, span),
            field_calls=_filter_usage(self.field_calls, span),
            dungeon_calls=_filter_usage(self.dungeon_calls, span),
            battle_calls=_filter_usage(self.battle_calls, span),
        )

    def find_procedures(self, text: str) -> list[ProcedureRecord]:
        needle = text.lower()
        return [record for record in self.procedures if needle in record.name.lower()]

    def message_ids_named(self, name: str) -> list[MessageIdRecord]:
        return [record for record in self.message_ids if record.name == name]

    def message_ids_for_flow(self, file: str) -> list[MessageIdRecord]:
        imports = [record.path for record in self.imports if _same_file(record.file, file)]
        if not imports:
            return []

        base = _parent_dir(file)
        expected_headers = {_join_rel(base, f"{import_path}.h") for import_path in imports}
        return [record for record in self.message_ids if _norm_file(record.file) in expected_headers]

    def message_id_for_flow(self, file: str, name: str) -> MessageIdRecord | None:
        for record in self.message_ids_for_flow(file):
            if record.name == name:
                return record
        return None

    def bit_usages(self, bit_id: int) -> list[BitUsage]:
        return [usage for usage in self.bits if usage.bit_id == bit_id]

    def used_bit_ids(self) -> set[int]:
        return {usage.bit_id for usage in self.bits if usage.bit_id is not None}

    def dynamic_bit_usages(self) -> list[BitUsage]:
        return [usage for usage in self.bits if usage.bit_id is None]

    def is_bit_used(self, bit_id: int) -> bool:
        return bit_id in self.used_bit_ids()

    def count_usages(self, count_id: int) -> list[CountUsage]:
        return [usage for usage in self.counts if usage.count_id == count_id]

    def event_calls_by_major(self, major: int | str) -> list[EventCallUsage]:
        expected = str(major)
        return [usage for usage in self.event_calls if usage.major == expected]

    def message_calls_named(self, name: str) -> list[MessageCallUsage]:
        return [usage for usage in self.message_calls if usage.name == name]

    def selection_calls_named(self, name: str) -> list[MessageCallUsage]:
        return [usage for usage in self.selection_calls if usage.name == name]

    def msg_var_usages(self, slot: int | None = None) -> list[MessageVarUsage]:
        if slot is None:
            return list(self.msg_vars)
        return [usage for usage in self.msg_vars if usage.slot == slot]

    def field_calls_by_major(self, major: int | str) -> list[TransitionCallUsage]:
        expected = str(major)
        return [usage for usage in self.field_calls if usage.first_arg == expected]

    def dungeon_calls_by_id(self, dungeon_id: int | str) -> list[TransitionCallUsage]:
        expected = str(dungeon_id)
        return [usage for usage in self.dungeon_calls if usage.first_arg == expected]

    def native_call(self, function: str) -> NativeCallSummary | None:
        for call in self.native_calls:
            if call.function == function:
                return call
        return None

    def procedure_report(self, file: str, procedure: str | int) -> str:
        from .reporting import render_procedure_report

        usages = self.procedure_usages(file, procedure)
        if not usages:
            return f"Procedure not found: {file}::{procedure}"
        return render_procedure_report(self, usages[0])

    def summary(self) -> dict[str, int]:
        return {
            "procedures": len(self.procedures),
            "procedure_spans": len(self.procedure_spans),
            "native_calls": len(self.native_calls),
            "message_tags": len(self.message_tags),
            "message_ids": len(self.message_ids),
            "imports": len(self.imports),
            "bit_usages": len(self.bits),
            "count_usages": len(self.counts),
            "event_calls": len(self.event_calls),
            "message_calls": len(self.message_calls),
            "selection_calls": len(self.selection_calls),
            "msg_var_usages": len(self.msg_vars),
            "field_calls": len(self.field_calls),
            "dungeon_calls": len(self.dungeon_calls),
            "battle_calls": len(self.battle_calls),
        }

    def _read_tsv(self, name: str) -> list[dict[str, str]]:
        path = self.indexes_dir / name
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def _scan_message_ids(self) -> Iterable[MessageIdRecord]:
        const_re = re.compile(r"^const\s+int\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+)\s*;")
        for path in self.decompiled_dir.rglob("*.msg.h"):
            rel = self._rel(path)
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                match = const_re.match(line.strip())
                if match:
                    yield MessageIdRecord(file=rel, name=match.group(1), value=int(match.group(2)))

    def _scan_flow_file(self, path: Path) -> None:
        rel = self._rel(path)
        import_re = re.compile(r'import\("([^"]+)"\);')
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        self.procedure_spans.extend(_scan_procedure_spans(rel, lines))

        for line_number, line in enumerate(lines, start=1):
            import_match = import_re.search(line)
            if import_match:
                self.imports.append(ImportRecord(file=rel, line=line_number, path=import_match.group(1)))

            for function, expression in _iter_calls(line, {"BIT_CHK", "BIT_ON", "BIT_OFF"}):
                self.bits.append(
                    BitUsage(
                        file=rel,
                        line=line_number,
                        function=function,
                        expression=expression,
                        bit_id=_try_eval_int(expression),
                    )
                )

            for function, expression in _iter_calls(line, {"GET_CNT", "SET_CNT"}):
                first_arg = _split_top_level_args(expression)[0] if expression.strip() else ""
                self.counts.append(
                    CountUsage(
                        file=rel,
                        line=line_number,
                        function=function,
                        expression=first_arg,
                        count_id=_try_eval_int(first_arg),
                    )
                )

            for _, expression in _iter_calls(line, {"CALL_EVENT"}):
                args = tuple(_split_top_level_args(expression))
                self.event_calls.append(EventCallUsage(file=rel, line=line_number, args=args))

            for function, expression in _iter_calls(line, {"MSG", "SEL"}):
                usage = MessageCallUsage(
                    file=rel,
                    line=line_number,
                    function=function,
                    expression=expression,
                    name=_try_identifier(expression),
                )
                if function == "MSG":
                    self.message_calls.append(usage)
                else:
                    self.selection_calls.append(usage)

            for _, expression in _iter_calls(line, {"SET_MSG_VAR"}):
                self.msg_vars.append(
                    MessageVarUsage(file=rel, line=line_number, args=tuple(_split_top_level_args(expression)))
                )

            for function, expression in _iter_calls(line, {"CALL_FIELD", "CALL_FIELD_SAFE"}):
                self.field_calls.append(
                    TransitionCallUsage(
                        file=rel,
                        line=line_number,
                        function=function,
                        args=tuple(_split_top_level_args(expression)),
                    )
                )

            for function, expression in _iter_calls(line, {"CALL_DUNGEON"}):
                self.dungeon_calls.append(
                    TransitionCallUsage(
                        file=rel,
                        line=line_number,
                        function=function,
                        args=tuple(_split_top_level_args(expression)),
                    )
                )

            for function, expression in _iter_calls(line, {"CALL_BATTLE"}):
                self.battle_calls.append(
                    TransitionCallUsage(
                        file=rel,
                        line=line_number,
                        function=function,
                        args=tuple(_split_top_level_args(expression)),
                    )
                )

    def _rel(self, path: Path) -> str:
        return str(path.relative_to(self.decompiled_dir))


def _iter_calls(line: str, names: set[str]) -> Iterable[tuple[str, str]]:
    for name in names:
        search_from = 0
        needle = f"{name}("
        while True:
            start = line.find(needle, search_from)
            if start == -1:
                break
            if start > 0 and _is_identifier_char(line[start - 1]):
                search_from = start + 1
                continue
            expr_start = start + len(needle)
            expr_end = _find_matching_paren(line, expr_start - 1)
            if expr_end != -1:
                yield name, line[expr_start:expr_end].strip()
                search_from = expr_end + 1
            else:
                break


def _scan_procedure_spans(file: str, lines: list[str]) -> list[ProcedureSpan]:
    index_re = re.compile(r"//\s*Procedure Index:\s*(\d+)")
    declaration_re = re.compile(r"^\s*(void|int|bool|float|string)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    spans: list[ProcedureSpan] = []
    pending_index: int | None = None

    for line_number, line in enumerate(lines, start=1):
        index_match = index_re.search(line)
        if index_match:
            pending_index = int(index_match.group(1))
            continue

        declaration_match = declaration_re.match(line)
        if declaration_match and pending_index is not None:
            if spans:
                previous = spans[-1]
                spans[-1] = ProcedureSpan(
                    file=previous.file,
                    procedure_index=previous.procedure_index,
                    return_type=previous.return_type,
                    name=previous.name,
                    start_line=previous.start_line,
                    end_line=line_number - 1,
                )

            spans.append(
                ProcedureSpan(
                    file=file,
                    procedure_index=pending_index,
                    return_type=declaration_match.group(1),
                    name=declaration_match.group(2),
                    start_line=line_number,
                    end_line=len(lines),
                )
            )
            pending_index = None

    return spans


def _find_matching_paren(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _split_top_level_args(text: str) -> list[str]:
    args: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            args.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        args.append(tail)
    return args


def _try_identifier(expression: str) -> str | None:
    expression = expression.strip()
    return expression if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", expression) else None


def _is_identifier_char(char: str) -> bool:
    return char.isalnum() or char == "_"


def _same_file(left: str, right: str) -> bool:
    return _norm_file(left) == _norm_file(right)


def _norm_file(path: str) -> str:
    return path.replace("\\", "/")


def _parent_dir(path: str) -> str:
    norm = _norm_file(path)
    return norm.rsplit("/", 1)[0] if "/" in norm else ""


def _join_rel(base: str, child: str) -> str:
    child_norm = _norm_file(child)
    if not base:
        return child_norm
    return f"{base}/{child_norm}"


def _filter_usage(items: list, span: ProcedureSpan) -> list:
    return [item for item in items if _same_file(item.file, span.file) and span.start_line <= item.line <= span.end_line]


def _try_eval_int(expression: str) -> int | None:
    expression = expression.strip()
    if not expression:
        return None
    if not re.fullmatch(r"[0-9a-fA-FxX()+\-*/%<>&|~\s]+", expression):
        return None
    try:
        value = eval(expression, {"__builtins__": {}}, {})
    except Exception:
        return None
    return value if isinstance(value, int) else None
