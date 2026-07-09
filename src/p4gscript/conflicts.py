from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .analyzer import WorkspaceAnalyzer, _iter_calls, _try_eval_int
from .project import P4GProject


@dataclass(frozen=True)
class ConflictReference:
    file: str
    line: int | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "detail": self.detail,
        }

    def render(self) -> str:
        location = f"{self.file}:{self.line}" if self.line is not None else self.file
        return f"{location} - {self.detail}" if self.detail else location


@dataclass(frozen=True)
class ConflictIssue:
    severity: str
    kind: str
    subject: str
    message: str
    total_references: int = 0
    references: tuple[ConflictReference, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "kind": self.kind,
            "subject": self.subject,
            "message": self.message,
            "total_references": self.total_references,
            "references": [reference.to_dict() for reference in self.references],
        }


@dataclass(frozen=True)
class ConflictReport:
    project: str
    workspace: str
    issues: tuple[ConflictIssue, ...] = field(default_factory=tuple)

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "info")

    @property
    def has_warnings(self) -> bool:
        return self.warning_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "workspace": self.workspace,
            "issue_count": len(self.issues),
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "issues": [issue.to_dict() for issue in self.issues],
        }

    def render(self) -> str:
        lines = [
            "P4GScript Conflict Report",
            "=========================",
            f"Project: {self.project}",
            f"Workspace: {self.workspace}",
            f"Issues: {len(self.issues)}",
            f"Warnings: {self.warning_count}",
            f"Info: {self.info_count}",
            "",
        ]

        if not self.issues:
            lines.append("No conflicts found.")
            return "\n".join(lines) + "\n"

        for issue in self.issues:
            lines.append(f"[{issue.severity.upper()}] {issue.kind}: {issue.subject}")
            lines.append(f"  {issue.message}")
            if issue.total_references:
                lines.append(f"  References: {issue.total_references}")
                for reference in issue.references:
                    lines.append(f"    - {reference.render()}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


def analyze_project_conflicts(
    project: P4GProject,
    workspace: WorkspaceAnalyzer,
    *,
    reference_limit: int = 5,
) -> ConflictReport:
    issues: list[ConflictIssue] = []

    for value, source_labels in sorted(_project_bit_references(project).items()):
        usages = workspace.bit_usages(value)
        if usages:
            issues.append(
                ConflictIssue(
                    severity="warning",
                    kind="bit",
                    subject=_format_bit_subject(value, source_labels),
                    message="This bit ID already appears in original scripts. Reusing it can change story, NPC, UI, or save-state behavior.",
                    total_references=len(usages),
                    references=tuple(
                        ConflictReference(
                            file=usage.file,
                            line=usage.line,
                            detail=f"{usage.function}({usage.expression})",
                        )
                        for usage in usages[:reference_limit]
                    ),
                )
            )

    for procedure in project.procedures:
        original_records = workspace.procedures_named(procedure.name)
        if original_records:
            issues.append(
                ConflictIssue(
                    severity="warning",
                    kind="procedure-name",
                    subject=procedure.name,
                    message="A generated procedure has the same name as an original procedure. This is dangerous unless you intentionally replace or import/hook the original script.",
                    total_references=len(original_records),
                    references=tuple(
                        ConflictReference(
                            file=record.file,
                            detail=f"procedure_index={record.procedure_index}",
                        )
                        for record in original_records[:reference_limit]
                    ),
                )
            )

        hook_target = _hook_target(procedure.name)
        if hook_target is not None:
            target_records = workspace.procedures_named(hook_target)
            if target_records:
                issues.append(
                    ConflictIssue(
                        severity="info",
                        kind="hook-target",
                        subject=f"{procedure.name} -> {hook_target}",
                        message="Hook target exists in original scripts. Verify that your build imports the correct original .bf before compiling with -Hook.",
                        total_references=len(target_records),
                        references=tuple(
                            ConflictReference(
                                file=record.file,
                                detail=f"procedure_index={record.procedure_index}",
                            )
                            for record in target_records[:reference_limit]
                        ),
                    )
                )
            else:
                issues.append(
                    ConflictIssue(
                        severity="warning",
                        kind="hook-target-missing",
                        subject=f"{procedure.name} -> {hook_target}",
                        message="Procedure name looks like a hook, but the target procedure was not found in the analyzed workspace.",
                    )
                )

    for message in project.messages:
        _append_message_name_issue(
            issues,
            workspace=workspace,
            name=message.name,
            kind="message-name",
            label="message",
            reference_limit=reference_limit,
        )

    for selection in project.selections:
        _append_message_name_issue(
            issues,
            workspace=workspace,
            name=selection.name,
            kind="selection-name",
            label="selection",
            reference_limit=reference_limit,
        )

    return ConflictReport(
        project=project.name,
        workspace=str(Path(workspace.root)),
        issues=tuple(issues),
    )


def _append_message_name_issue(
    issues: list[ConflictIssue],
    *,
    workspace: WorkspaceAnalyzer,
    name: str,
    kind: str,
    label: str,
    reference_limit: int,
) -> None:
    records = workspace.message_ids_named(name)
    if not records:
        return

    issues.append(
        ConflictIssue(
            severity="warning",
            kind=kind,
            subject=name,
            message=f"A generated {label} name already exists in original MessageScript headers. Rename it or make sure this is an intentional replacement.",
            total_references=len(records),
            references=tuple(
                ConflictReference(
                    file=record.file,
                    detail=f"id={record.value}",
                )
                for record in records[:reference_limit]
            ),
        )
    )


def _hook_target(name: str) -> str | None:
    for suffix in ("_hookafter", "_softhook", "_hook"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def _project_bit_references(project: P4GProject) -> dict[int, set[str]]:
    references: dict[int, set[str]] = {}
    for name, value in project.bit_constants.items():
        references.setdefault(value, set()).add(f"{name}={value}")

    try:
        flow_text = project.render_flow()
    except Exception:
        return references

    for line_number, line in enumerate(flow_text.splitlines(), start=1):
        for function, expression in _iter_calls(line, {"BIT_CHK", "BIT_ON", "BIT_OFF"}):
            value = _try_eval_int(expression)
            if value is not None:
                references.setdefault(value, set()).add(f"line {line_number}: {function}({expression})")

    return references


def _format_bit_subject(value: int, source_labels: set[str]) -> str:
    named = sorted(label for label in source_labels if not label.startswith("line "))
    if named:
        return ", ".join(named)
    return f"raw bit {value}"
