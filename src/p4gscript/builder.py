from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any

from .analyzer import WorkspaceAnalyzer
from .compiler import CompileResult
from .conflicts import ConflictReport, analyze_project_conflicts
from .exceptions import P4GScriptError
from .project import P4GProject
from .safety import normalize_safety


@dataclass(frozen=True)
class BuildResult:
    project: P4GProject
    out_dir: Path
    flow_path: Path
    msg_path: Path | None
    bf_path: Path | None
    manifest_json_path: Path
    manifest_txt_path: Path
    conflicts_txt_path: Path | None
    package_dir: Path | None
    safety: str
    allow_conflicts: bool
    safety_errors: tuple[str, ...]
    copied_imports: tuple[tuple[Path, Path], ...] = ()
    packaged_files: tuple[tuple[Path, Path], ...] = ()
    compile_result: CompileResult | None = None
    conflict_report: ConflictReport | None = None

    @property
    def blocked(self) -> bool:
        return bool(self.safety_errors) and not self.allow_conflicts


def load_project_from_file(path: str | Path) -> P4GProject:
    module_path = Path(path).resolve()
    if not module_path.exists():
        raise P4GScriptError(f"Project file does not exist: {module_path}")

    module = _load_module(module_path)
    build_project = getattr(module, "build_project", None)
    if build_project is None or not callable(build_project):
        raise P4GScriptError(f"Project file must define callable build_project(): {module_path}")

    project = build_project()
    if not isinstance(project, P4GProject):
        raise P4GScriptError("build_project() must return P4GProject")
    return project


def build_project(
    project: P4GProject,
    out_dir: str | Path,
    *,
    compile_bf: bool = False,
    compiler_path: str | Path | None = None,
    hook: bool | None = None,
    workspace: str | Path | WorkspaceAnalyzer | None = None,
    safety: str | None = None,
    allow_conflicts: bool = False,
    package_out: str | Path | None = None,
    debug: bool = False,
) -> BuildResult:
    out_path = Path(out_dir)
    workspace_analyzer = _resolve_workspace(workspace)
    safety_mode = _resolve_safety(project, safety)
    conflict_report: ConflictReport | None = None
    if workspace_analyzer is not None:
        project.attach_analyzer(workspace_analyzer)
        conflict_report = analyze_project_conflicts(project, workspace_analyzer)

    _validate_project_mode(project, compile_bf=compile_bf)

    flow_path, msg_path = project.write(out_path)
    copied_imports = tuple(_copy_project_imports(project, out_path))
    safety_errors = tuple(_evaluate_safety(project, conflict_report, safety_mode))

    compile_result: CompileResult | None = None
    bf_path: Path | None = None
    blocked = bool(safety_errors) and not allow_conflicts
    compile_hook = project.requires_hook if hook is None else (hook or project.requires_hook)
    if compile_bf and not blocked:
        compile_result = project.compile(out_path, compiler_path=compiler_path, hook=compile_hook, debug=debug)
        bf_path = out_path / f"{project.name}.bf"

    packaged_files = tuple(_package_project_output(project, bf_path, package_out))

    result = BuildResult(
        project=project,
        out_dir=out_path,
        flow_path=flow_path,
        msg_path=msg_path,
        bf_path=bf_path,
        compile_result=compile_result,
        conflict_report=conflict_report,
        manifest_json_path=out_path / "manifest.json",
        manifest_txt_path=out_path / "manifest.txt",
        conflicts_txt_path=out_path / "conflicts.txt" if conflict_report is not None else None,
        package_dir=Path(package_out) if package_out is not None else None,
        safety=safety_mode,
        allow_conflicts=allow_conflicts,
        safety_errors=safety_errors,
        copied_imports=copied_imports,
        packaged_files=packaged_files,
    )
    write_build_manifest(result)
    return result


def build_project_file(
    path: str | Path,
    out_dir: str | Path,
    *,
    compile_bf: bool = False,
    compiler_path: str | Path | None = None,
    hook: bool | None = None,
    workspace: str | Path | WorkspaceAnalyzer | None = None,
    safety: str | None = None,
    allow_conflicts: bool = False,
    package_out: str | Path | None = None,
    debug: bool = False,
) -> BuildResult:
    project = load_project_from_file(path)
    return build_project(
        project,
        out_dir,
        compile_bf=compile_bf,
        compiler_path=compiler_path,
        hook=hook,
        workspace=workspace,
        safety=safety,
        allow_conflicts=allow_conflicts,
        package_out=package_out,
        debug=debug,
    )


def write_build_manifest(result: BuildResult) -> None:
    data = build_manifest_data(result)
    if result.conflicts_txt_path is not None and result.conflict_report is not None:
        result.conflicts_txt_path.write_text(result.conflict_report.render(), encoding="utf-8")
    result.manifest_json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result.manifest_txt_path.write_text(render_build_manifest(data), encoding="utf-8")


def build_manifest_data(result: BuildResult) -> dict[str, Any]:
    project = result.project
    generated = {
        "flow": str(result.flow_path),
        "msg": str(result.msg_path) if result.msg_path else None,
        "bf": str(result.bf_path) if result.bf_path else None,
        "manifest_json": str(result.manifest_json_path),
        "manifest_txt": str(result.manifest_txt_path),
        "conflicts_txt": str(result.conflicts_txt_path) if result.conflicts_txt_path else None,
    }

    return {
        "project": project.name,
        "library": project.library,
        "encoding": project.encoding,
        "out_format": project.out_format,
        "create_script": project.create_script,
        "build_mode": "create" if project.create_script else "patch",
        "generated": generated,
        "warnings": list(project.warnings),
        "target_path": project.target_path,
        "requires_hook": project.requires_hook,
        "package_dir": str(result.package_dir) if result.package_dir else None,
        "imports": [item.to_dict() for item in project.imports],
        "copied_imports": [
            {"source": str(source), "destination": str(destination)}
            for source, destination in result.copied_imports
        ],
        "packaged_files": [
            {"source": str(source), "destination": str(destination)}
            for source, destination in result.packaged_files
        ],
        "messages": [message.name for message in project.messages],
        "selections": [selection.name for selection in project.selections],
        "procedures": [procedure.name for procedure in project.procedures],
        "bit_constants": dict(sorted(project.bit_constants.items())),
        "bit_reservations": {name: reservation.to_dict() for name, reservation in sorted(project.bit_reservations.items())},
        "conflicts": result.conflict_report.to_dict() if result.conflict_report is not None else None,
        "safety": {
            "mode": result.safety,
            "allow_conflicts": result.allow_conflicts,
            "blocked": result.blocked,
            "errors": list(result.safety_errors),
        },
        "compile": {
            "ran": result.compile_result is not None,
            "command": result.compile_result.command if result.compile_result else None,
            "returncode": result.compile_result.returncode if result.compile_result else None,
        },
    }


def render_build_manifest(data: dict[str, Any]) -> str:
    lines = [
        "P4GScript Build Manifest",
        "========================",
        f"Project: {data['project']}",
        f"Library: {data['library']}",
        f"Encoding: {data['encoding']}",
        f"OutFormat: {data['out_format']}",
        f"Build mode: {data['build_mode']}",
        f"Create script: {data['create_script']}",
        "",
        "Generated:",
    ]
    for key, value in data["generated"].items():
        if value:
            lines.append(f"  {key}: {value}")

    lines.extend(["", "Warnings:"])
    if data["warnings"]:
        lines.extend(f"  - {warning}" for warning in data["warnings"])
    else:
        lines.append("  none")

    lines.extend(["", "Target:"])
    lines.append(f"  path: {data['target_path'] or 'not set'}")
    lines.append(f"  requires_hook: {data['requires_hook']}")

    lines.extend(["", "Imports:"])
    if data["imports"]:
        for item in data["imports"]:
            copy_text = "copy" if item["copy"] else "no-copy"
            lines.append(f"  - {item['kind']}: {item['import_path']} <- {item['source']} ({copy_text})")
    else:
        lines.append("  none")

    lines.extend(["", "Copied Imports:"])
    if data["copied_imports"]:
        for item in data["copied_imports"]:
            lines.append(f"  - {item['source']} -> {item['destination']}")
    else:
        lines.append("  none")

    lines.extend(["", "Package:"])
    lines.append(f"  dir: {data['package_dir'] or 'not written'}")
    if data["packaged_files"]:
        for item in data["packaged_files"]:
            lines.append(f"  - {item['source']} -> {item['destination']}")
    else:
        lines.append("  files: none")

    lines.extend(["", "Messages:"])
    lines.extend(_render_list(data["messages"]))

    lines.extend(["", "Selections:"])
    lines.extend(_render_list(data["selections"]))

    lines.extend(["", "Procedures:"])
    lines.extend(_render_list(data["procedures"]))

    lines.extend(["", "Bit Constants:"])
    if data["bit_constants"]:
        lines.extend(f"  - {name} = {value}" for name, value in data["bit_constants"].items())
    else:
        lines.append("  none")

    lines.extend(["", "Bit Reservations:"])
    if data["bit_reservations"]:
        for name, reservation in data["bit_reservations"].items():
            lines.append(
                f"  - {name}: {reservation['value']} "
                f"(range {reservation['range_start']}..{reservation['range_end']})"
            )
    else:
        lines.append("  none")

    compile_data = data["compile"]
    lines.extend(["", "Compile:"])
    lines.append(f"  ran: {compile_data['ran']}")
    if compile_data["command"]:
        lines.append(f"  command: {' '.join(compile_data['command'])}")
        lines.append(f"  returncode: {compile_data['returncode']}")

    conflict_data = data["conflicts"]
    lines.extend(["", "Conflicts:"])
    if conflict_data is None:
        lines.append("  workspace: not checked")
    else:
        lines.append(f"  workspace: {conflict_data['workspace']}")
        lines.append(f"  issues: {conflict_data['issue_count']}")
        lines.append(f"  warnings: {conflict_data['warning_count']}")
        lines.append(f"  info: {conflict_data['info_count']}")

    safety_data = data["safety"]
    lines.extend(["", "Safety:"])
    lines.append(f"  mode: {safety_data['mode']}")
    lines.append(f"  allow_conflicts: {safety_data['allow_conflicts']}")
    lines.append(f"  blocked: {safety_data['blocked']}")
    if safety_data["errors"]:
        lines.extend(f"  - {error}" for error in safety_data["errors"])
    else:
        lines.append("  errors: none")

    return "\n".join(lines) + "\n"


def _render_list(values: list[str]) -> list[str]:
    if not values:
        return ["  none"]
    return [f"  - {value}" for value in values]


def _load_module(path: Path) -> ModuleType:
    module_name = f"p4gscript_project_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise P4GScriptError(f"Cannot load project file: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_workspace(workspace: str | Path | WorkspaceAnalyzer | None) -> WorkspaceAnalyzer | None:
    if workspace is None:
        return None
    if isinstance(workspace, WorkspaceAnalyzer):
        return workspace
    return WorkspaceAnalyzer.load(workspace)


def _copy_project_imports(project: P4GProject, out_dir: Path) -> list[tuple[Path, Path]]:
    copied: list[tuple[Path, Path]] = []
    for item in project.imports:
        if not item.copy:
            continue

        source = Path(item.source)
        if not source.exists():
            raise P4GScriptError(f"Imported file does not exist: {source}")
        destination = out_dir / item.import_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append((source, destination))
    return copied


def _package_project_output(
    project: P4GProject,
    bf_path: Path | None,
    package_out: str | Path | None,
) -> list[tuple[Path, Path]]:
    if package_out is None:
        return []
    if project.target_path is None:
        raise P4GScriptError("Package output requires project.target('path/in/game.bf')")
    if bf_path is None or not bf_path.exists():
        raise P4GScriptError("Package output requires a compiled .bf; pass --compile")

    package_dir = Path(package_out)
    destination = package_dir / project.target_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bf_path, destination)

    install_manifest = {
        "project": project.name,
        "target_path": project.target_path,
        "source_bf": str(bf_path),
        "packaged_bf": str(destination),
        "requires_hook": project.requires_hook,
        "create_script": project.create_script,
        "build_mode": "create" if project.create_script else "patch",
    }
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "p4gscript_install_manifest.json").write_text(
        json.dumps(install_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return [(bf_path, destination)]


def _validate_project_mode(project: P4GProject, *, compile_bf: bool) -> None:
    if project.create_script and project.requires_hook:
        raise P4GScriptError(
            "Hook procedures patch existing scripts. Use create_script=False for patch builds, "
            "or use project.procedure(...) when creating a new script."
        )

    has_bf_import = any(item.kind == "bf" for item in project.imports)
    if compile_bf and not project.create_script and project.requires_hook and not has_bf_import:
        raise P4GScriptError(
            "Patch builds with hooks need an original .bf import. Call project.import_bf(...), "
            "or set create_script=True and avoid hook procedures."
        )

def _resolve_safety(project: P4GProject, safety: str | None) -> str:
    return normalize_safety(safety, default=project.safety)


def _evaluate_safety(project: P4GProject, conflict_report: ConflictReport | None, safety: str) -> list[str]:
    if safety == "expert":
        return []

    errors: list[str] = []

    if conflict_report is not None and conflict_report.has_warnings:
        warning_count = conflict_report.warning_count
        if safety == "beginner":
            errors.append(f"Conflict report contains {warning_count} warning(s)")

    unsafe_bits = [warning for warning in project.warnings if warning.startswith("Unsafe bit ")]
    if safety == "beginner" and unsafe_bits:
        errors.extend(unsafe_bits)

    return errors



