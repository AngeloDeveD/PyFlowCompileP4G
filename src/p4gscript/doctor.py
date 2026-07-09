from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from .compiler import bundled_compiler_path, resolve_compiler_path


@dataclass(frozen=True)
class DoctorCheck:
    status: str
    name: str
    detail: str

    @property
    def is_error(self) -> bool:
        return self.status == "error"


@dataclass(frozen=True)
class DoctorReport:
    checks: list[DoctorCheck]

    @property
    def has_errors(self) -> bool:
        return any(check.is_error for check in self.checks)

    def render(self) -> str:
        lines = ["P4GScript Doctor", "================"]
        for check in self.checks:
            lines.append(f"[{check.status.upper()}] {check.name}: {check.detail}")
        return "\n".join(lines) + "\n"


def run_doctor(
    *,
    workspace: str | Path | None = None,
    compiler_path: str | Path | None = None,
    ast_root: str | Path | None = None,
) -> DoctorReport:
    checks: list[DoctorCheck] = []
    checks.extend(_python_checks())

    if workspace is not None:
        checks.extend(_workspace_checks(Path(workspace)))
    else:
        checks.append(DoctorCheck("warn", "workspace", "not provided"))

    if ast_root is not None:
        root = Path(ast_root)
    else:
        root = _guess_ast_root()
    checks.extend(_ast_root_checks(root))

    checks.extend(_compiler_checks(compiler_path, root))

    return DoctorReport(checks=checks)


def _python_checks() -> list[DoctorCheck]:
    return [
        DoctorCheck("ok", "python", sys.version.split()[0]),
        DoctorCheck("ok", "platform", platform.platform()),
    ]


def _workspace_checks(workspace: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    if workspace.exists():
        checks.append(DoctorCheck("ok", "workspace", str(workspace)))
    else:
        checks.append(DoctorCheck("error", "workspace", f"missing: {workspace}"))
        return checks

    decompiled = workspace / "decompiled"
    indexes = workspace / "indexes"
    checks.append(_exists_check("decompiled", decompiled, required=True))
    checks.append(_exists_check("indexes", indexes, required=True))

    for name in ("procedures.tsv", "native_calls.tsv", "message_tags.tsv"):
        checks.append(_exists_check(f"index {name}", indexes / name, required=True))

    if decompiled.exists():
        flow_count = _count_files(decompiled, "*.flow")
        msg_count = _count_files(decompiled, "*.msg")
        msg_h_count = _count_files(decompiled, "*.msg.h")
        checks.append(DoctorCheck("ok" if flow_count else "warn", "flow files", str(flow_count)))
        checks.append(DoctorCheck("ok" if msg_count else "warn", "msg files", str(msg_count)))
        checks.append(DoctorCheck("ok" if msg_h_count else "warn", "msg.h files", str(msg_h_count)))

    return checks


def _ast_root_checks(root: Path | None) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    if root is None:
        return [DoctorCheck("warn", "ast root", "not found automatically")]

    checks.append(DoctorCheck("ok" if root.exists() else "error", "ast root", str(root)))
    checks.append(_exists_check("Libraries", root / "Source" / "AtlusScriptLibrary" / "Libraries", required=False))
    checks.append(_exists_check("Charsets", root / "Source" / "AtlusScriptLibrary" / "Charsets", required=False))
    checks.append(_exists_check("P4G library", root / "Source" / "AtlusScriptLibrary" / "Libraries" / "Persona4Golden.json", required=False))
    checks.append(_exists_check("P4G message library", root / "Source" / "AtlusScriptLibrary" / "Libraries" / "Persona4Golden" / "MessageScriptLibrary.json", required=False))
    return checks


def _compiler_checks(compiler_path: str | Path | None, root: Path | None) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    try:
        resolved = resolve_compiler_path(compiler_path)
    except Exception:
        resolved = None

    if resolved is not None:
        checks.append(DoctorCheck("ok", "AtlusScriptCompiler", str(resolved)))
        if resolved == bundled_compiler_path():
            checks.append(DoctorCheck("ok", "bundled compiler", str(bundled_compiler_path().parent)))
        try:
            completed = subprocess.run([str(resolved), "-Help"], capture_output=True, text=True, check=False, timeout=15, cwd=str(resolved.parent))
        except Exception as exc:
            checks.append(DoctorCheck("warn", "AtlusScriptCompiler -Help", str(exc)))
            return checks

        status = "ok" if completed.returncode == 0 else "warn"
        detail = f"return code {completed.returncode}"
        checks.append(DoctorCheck(status, "AtlusScriptCompiler -Help", detail))
        return checks

    candidates: list[Path | str] = []
    if compiler_path is not None:
        candidates.append(Path(compiler_path))
    if root is not None:
        candidates.extend(root.rglob("AtlusScriptCompiler.exe"))
    candidates.append("AtlusScriptCompiler")

    found = None
    for candidate in candidates:
        if isinstance(candidate, Path):
            if candidate.exists():
                found = str(candidate)
                break
        else:
            resolved = shutil.which(candidate)
            if resolved:
                found = resolved
                break

    if found is None:
        checks.append(DoctorCheck("warn", "AtlusScriptCompiler", "not found; bundle compiler files or pass compiler_path"))
        return checks

    checks.append(DoctorCheck("ok", "AtlusScriptCompiler", found))
    try:
        completed = subprocess.run([found, "-Help"], capture_output=True, text=True, check=False, timeout=15)
    except Exception as exc:
        checks.append(DoctorCheck("warn", "AtlusScriptCompiler -Help", str(exc)))
        return checks

    status = "ok" if completed.returncode == 0 else "warn"
    detail = f"return code {completed.returncode}"
    checks.append(DoctorCheck(status, "AtlusScriptCompiler -Help", detail))
    return checks


def _exists_check(name: str, path: Path, *, required: bool) -> DoctorCheck:
    if path.exists():
        return DoctorCheck("ok", name, str(path))
    return DoctorCheck("error" if required else "warn", name, f"missing: {path}")


def _count_files(root: Path, pattern: str) -> int:
    return sum(1 for _ in root.rglob(pattern))


def _guess_ast_root() -> Path | None:
    current = Path.cwd()
    for candidate in [current, *current.parents]:
        if (candidate / "Source" / "AtlusScriptCompiler").exists():
            return candidate
    return None
