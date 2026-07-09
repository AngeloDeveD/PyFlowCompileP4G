from __future__ import annotations

import argparse
import difflib
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SDK_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SDK_ROOT / "src"
THIS_DIR = Path(__file__).resolve().parent
GOLDEN_DIR = THIS_DIR / "golden"
DEFAULT_OUT = THIS_DIR / "build"
DEFAULT_WORKSPACE = REPO_ROOT / "Samples" / "P4G_Steam_Test" / "script_workspace"
DEFAULT_COMPILER = REPO_ROOT / "Build" / "Release" / "net8.0" / "AtlusScriptCompiler.exe"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from p4gscript import build_project  # noqa: E402
from python_event_project import build_project as build_python_event  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Python SDK -> .flow/.msg -> .bf pipeline.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output directory for generated files.")
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE), help="script_workspace used for safety/conflict checks.")
    parser.add_argument("--compiler", default=str(DEFAULT_COMPILER), help="AtlusScriptCompiler.exe path.")
    parser.add_argument("--no-compile", action="store_true", help="Skip .flow -> .bf compilation.")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    workspace = Path(args.workspace)
    compiler = Path(args.compiler)

    project = build_python_event()
    workspace_arg = workspace if workspace.exists() else None
    result = build_project(
        project,
        out_dir,
        workspace=workspace_arg,
        safety="beginner",
        allow_conflicts=workspace_arg is None,
        compile_bf=not args.no_compile and compiler.exists(),
        compiler_path=compiler,
    )

    checks = [
        compare_text(result.flow_path, GOLDEN_DIR / "python_event.flow"),
        compare_text(result.msg_path, GOLDEN_DIR / "python_event.msg") if result.msg_path else ("msg", False),
    ]

    print("Generated:")
    print(f"  flow: {result.flow_path}")
    print(f"  msg:  {result.msg_path}")
    print(f"  bf:   {result.bf_path}")
    print(f"  manifest: {result.manifest_txt_path}")
    print(f"  conflicts: {result.conflicts_txt_path}")
    print()

    failed = False
    for label, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'} {label}")
        failed = failed or not ok

    if result.blocked:
        failed = True
        print("FAIL safety policy blocked the build:")
        for error in result.safety_errors:
            print(f"  - {error}")

    if args.no_compile:
        print("SKIP compiler check (--no-compile)")
    elif not compiler.exists():
        failed = True
        print(f"FAIL compiler missing: {compiler}")
    elif result.bf_path is None or not result.bf_path.exists() or result.bf_path.stat().st_size == 0:
        failed = True
        print("FAIL .bf was not produced or is empty")
    else:
        print(f"PASS compiled .bf ({result.bf_path.stat().st_size} bytes)")

    if result.conflict_report is not None:
        if result.conflict_report.has_warnings:
            failed = True
            print(f"FAIL conflict report has {result.conflict_report.warning_count} warning(s)")
        else:
            print("PASS conflict report has no warnings")

    return 1 if failed else 0


def compare_text(actual_path: Path, expected_path: Path) -> tuple[str, bool]:
    actual = normalize(actual_path.read_text(encoding="utf-8"))
    expected = normalize(expected_path.read_text(encoding="utf-8"))
    label = f"{actual_path.name} matches {expected_path.name}"
    if actual == expected:
        return label, True

    diff = difflib.unified_diff(
        expected.splitlines(),
        actual.splitlines(),
        fromfile=str(expected_path),
        tofile=str(actual_path),
        lineterm="",
    )
    print("\n".join(diff))
    return label, False


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").strip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
