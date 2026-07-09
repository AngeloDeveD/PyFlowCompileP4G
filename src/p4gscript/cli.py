from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .analyzer import WorkspaceAnalyzer
from .builder import build_project_file
from .doctor import run_doctor
from .safety import SAFETY_CHOICES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="p4gscript",
        description="Persona 4 Golden script SDK command line tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary = subparsers.add_parser("summary", help="Print workspace analyzer summary.")
    _add_workspace_arg(summary)
    summary.set_defaults(func=_cmd_summary)

    report = subparsers.add_parser("report", help="Print a procedure usage report.")
    _add_workspace_arg(report)
    report.add_argument("--file", required=True, help="Flow file path relative to decompiled workspace.")
    report.add_argument("--procedure", required=True, help="Procedure name or index.")
    report.set_defaults(func=_cmd_report)

    find = subparsers.add_parser("find-procedure", help="Find procedures by name substring.")
    _add_workspace_arg(find)
    find.add_argument("text", help="Case-insensitive substring to search for.")
    find.add_argument("--limit", type=int, default=25, help="Maximum rows to print.")
    find.set_defaults(func=_cmd_find_procedure)

    message = subparsers.add_parser("message", help="Find message IDs and MSG usages by name.")
    _add_workspace_arg(message)
    message.add_argument("name", help="Message or selection constant name.")
    message.add_argument("--limit", type=int, default=25, help="Maximum rows per section.")
    message.set_defaults(func=_cmd_message)

    bit = subparsers.add_parser("bit", help="Find BIT_* usages by numeric bit ID.")
    _add_workspace_arg(bit)
    bit.add_argument("id", type=int, help="Bit ID to search for.")
    bit.add_argument("--limit", type=int, default=25, help="Maximum rows to print.")
    bit.set_defaults(func=_cmd_bit)

    doctor = subparsers.add_parser("doctor", help="Check workspace, compiler, and SDK environment.")
    doctor.add_argument("--workspace", help="Path to script_workspace containing decompiled/ and indexes/.")
    doctor.add_argument("--compiler", help="Path to AtlusScriptCompiler executable.")
    doctor.add_argument("--ast-root", help="Path to Atlus Script Tools root.")
    doctor.set_defaults(func=_cmd_doctor)

    build = subparsers.add_parser("build", help="Build .flow/.msg from a Python project file.")
    build.add_argument("project_file", help="Python file defining build_project().")
    build.add_argument("--out", required=True, help="Output directory.")
    build.add_argument("--compile", action="store_true", help="Also compile generated .flow into .bf.")
    build.add_argument("--compiler", help="Path to AtlusScriptCompiler executable. If omitted, p4gscript tries the bundled compiler first.")
    build.add_argument("--hook", action="store_true", help="Pass -Hook while compiling.")
    build.add_argument("--workspace", help="Optional script_workspace path for conflict checks.")
    build.add_argument("--safety", choices=SAFETY_CHOICES, help="Safety policy for generated project.")
    build.add_argument("--allow-conflicts", action="store_true", help="Do not block when the selected safety policy reports errors.")
    build.add_argument("--package-out", help="Optional package directory; requires --compile and project.target(...).")
    build.add_argument("--debug", action="store_true", help="Print AtlusScriptCompiler command and stdout/stderr while compiling.")
    build.set_defaults(func=_cmd_build)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _add_workspace_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        required=True,
        help="Path to script_workspace containing decompiled/ and indexes/.",
    )


def _load_workspace(args: argparse.Namespace) -> WorkspaceAnalyzer:
    workspace_path = Path(args.workspace)
    if not workspace_path.exists():
        raise SystemExit(f"Workspace does not exist: {workspace_path}")
    return WorkspaceAnalyzer.load(workspace_path)


def _cmd_summary(args: argparse.Namespace) -> int:
    workspace = _load_workspace(args)
    for key, value in workspace.summary().items():
        print(f"{key}: {value}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    workspace = _load_workspace(args)
    procedure: str | int = args.procedure
    if str(procedure).isdigit():
        procedure = int(procedure)
    print(workspace.procedure_report(args.file, procedure), end="")
    return 0


def _cmd_find_procedure(args: argparse.Namespace) -> int:
    workspace = _load_workspace(args)
    records = workspace.find_procedures(args.text)[: args.limit]
    for record in records:
        print(f"{record.file}:{record.procedure_index}: {record.return_type} {record.name}")
    if not records:
        print("No procedures found.")
    return 0


def _cmd_message(args: argparse.Namespace) -> int:
    workspace = _load_workspace(args)

    ids = workspace.message_ids_named(args.name)[: args.limit]
    print(f"Message IDs for {args.name}: {len(ids)} shown")
    for item in ids:
        print(f"  {item.file}: {item.value}")

    message_calls = workspace.message_calls_named(args.name)[: args.limit]
    print(f"MSG usages for {args.name}: {len(message_calls)} shown")
    for usage in message_calls:
        print(f"  {usage.file}:{usage.line}")

    selection_calls = workspace.selection_calls_named(args.name)[: args.limit]
    print(f"SEL usages for {args.name}: {len(selection_calls)} shown")
    for usage in selection_calls:
        print(f"  {usage.file}:{usage.line}")

    return 0


def _cmd_bit(args: argparse.Namespace) -> int:
    workspace = _load_workspace(args)
    usages = workspace.bit_usages(args.id)[: args.limit]
    print(f"BIT usages for {args.id}: {len(usages)} shown")
    for usage in usages:
        print(f"  {usage.file}:{usage.line}: {usage.function}({usage.expression})")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    report = run_doctor(workspace=args.workspace, compiler_path=args.compiler, ast_root=args.ast_root)
    print(report.render(), end="")
    return 1 if report.has_errors else 0


def _cmd_build(args: argparse.Namespace) -> int:
    result = build_project_file(
        args.project_file,
        args.out,
        compile_bf=args.compile,
        compiler_path=args.compiler,
        hook=args.hook,
        workspace=args.workspace,
        safety=args.safety,
        allow_conflicts=args.allow_conflicts,
        package_out=args.package_out,
        debug=args.debug,
    )
    print(f"Wrote {result.flow_path}")
    if result.msg_path:
        print(f"Wrote {result.msg_path}")
    if result.bf_path:
        print(f"Wrote {result.bf_path}")
    print(f"Wrote {result.manifest_json_path}")
    print(f"Wrote {result.manifest_txt_path}")
    if result.conflicts_txt_path:
        print(f"Wrote {result.conflicts_txt_path}")
    for _, destination in result.packaged_files:
        print(f"Packaged {destination}")

    if result.project.warnings:
        print("Warnings:")
        for warning in result.project.warnings:
            print(f"  - {warning}")

    if result.conflict_report is not None:
        print(
            "Conflicts: "
            f"{len(result.conflict_report.issues)} issue(s), "
            f"{result.conflict_report.warning_count} warning(s)"
        )
    if result.blocked:
        print("Safety blocked build before .bf compilation:")
        for error in result.safety_errors:
            print(f"  - {error}")
        print("Use --allow-conflicts only if this is intentional.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


