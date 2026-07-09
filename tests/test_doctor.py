from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from p4gscript import run_doctor
from p4gscript.cli import main


def test_doctor_api_for_workspace():
    repo_root = Path(__file__).resolve().parents[2]
    workspace = repo_root / "Samples" / "P4G_Steam_Test" / "script_workspace"
    if not workspace.exists():
        return

    report = run_doctor(workspace=workspace, ast_root=repo_root)
    rendered = report.render()

    assert "P4GScript Doctor" in rendered
    assert "[OK] workspace" in rendered
    assert "[OK] decompiled" in rendered
    assert "[OK] indexes" in rendered
    assert "flow files" in rendered


def test_doctor_cli_for_workspace():
    repo_root = Path(__file__).resolve().parents[2]
    workspace = repo_root / "Samples" / "P4G_Steam_Test" / "script_workspace"
    if not workspace.exists():
        return

    # Doctor may return 0 or 1 depending on whether optional local compiler files exist,
    # but it should always print a useful report.
    buffer = StringIO()
    with redirect_stdout(buffer):
        result = main(["doctor", "--workspace", str(workspace), "--ast-root", str(repo_root)])
    assert result in {0, 1}
    assert "P4GScript Doctor" in buffer.getvalue()
