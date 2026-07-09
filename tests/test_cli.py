from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from p4gscript.cli import main


def _workspace() -> Path:
    return Path(__file__).resolve().parents[2] / "Samples" / "P4G_Steam_Test" / "script_workspace"


def test_cli_summary():
    workspace = _workspace()
    if not workspace.exists():
        return

    output = _run_cli(["summary", "--workspace", str(workspace)])
    assert "procedures: 29232" in output
    assert "message_calls: 36908" in output


def test_cli_report():
    workspace = _workspace()
    if not workspace.exists():
        return

    output = _run_cli(
        [
            "report",
            "--workspace",
            str(workspace),
            "--file",
            "data_e.cpk/field/script/comu00.flow",
            "--procedure",
            "SCR_ONLY_NPC_YOUSUKE",
        ]
    )
    assert "Procedure Report" in output
    assert "SCR_ONLY_NPC_YOUSUKE" in output
    assert "Selection Calls: 4" in output


def test_cli_message():
    workspace = _workspace()
    if not workspace.exists():
        return

    output = _run_cli(["message", "--workspace", str(workspace), "YOUSUKE_DUNGEON_SEL_2"])
    assert "Message IDs for YOUSUKE_DUNGEON_SEL_2" in output
    assert "SEL usages for YOUSUKE_DUNGEON_SEL_2" in output


def test_cli_doctor():
    workspace = _workspace()
    if not workspace.exists():
        return

    output = _run_cli_allowing_status(["doctor", "--workspace", str(workspace), "--ast-root", str(workspace.parents[2])])
    assert "P4GScript Doctor" in output
    assert "[OK] workspace" in output


def _run_cli(argv: list[str]) -> str:
    buffer = StringIO()
    with redirect_stdout(buffer):
        assert main(argv) == 0
    return buffer.getvalue()


def _run_cli_allowing_status(argv: list[str]) -> str:
    buffer = StringIO()
    with redirect_stdout(buffer):
        assert main(argv) in {0, 1}
    return buffer.getvalue()
