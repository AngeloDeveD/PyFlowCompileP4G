import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from p4gscript import P4GProject, bit, build_project, build_project_file, load_project_from_file
from p4gscript.cli import main


def _example_project() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "mod_project.py"


def test_load_project_from_file():
    project = load_project_from_file(_example_project())

    assert project.name == "mod_hello"
    assert project.messages[0].name == "MOD_HELLO"
    assert project.procedures[0].name == "MOD_HELLO_TEST"


def test_build_project_file():
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        result = build_project_file(_example_project(), tmp_path)

        assert result.flow_path.exists()
        assert result.msg_path is not None and result.msg_path.exists()
        assert result.manifest_json_path.exists()
        assert result.manifest_txt_path.exists()

        flow = result.flow_path.read_text(encoding="utf-8")
        msg = result.msg_path.read_text(encoding="utf-8")
        manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))

        assert 'import("mod_hello.msg");' in flow
        assert "const int MOD_HELLO_DONE = 9000;" in flow
        assert "[msg MOD_HELLO [Yosuke]]" in msg
        assert manifest["project"] == "mod_hello"
        assert manifest["bit_constants"]["MOD_HELLO_DONE"] == 9000


def test_cli_build():
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        buffer = StringIO()
        with redirect_stdout(buffer):
            assert main(["build", str(_example_project()), "--out", str(tmp_path)]) == 0

        assert (tmp_path / "mod_hello.flow").exists()
        assert (tmp_path / "mod_hello.msg").exists()
        assert (tmp_path / "manifest.json").exists()
        assert "Wrote" in buffer.getvalue()


def test_build_project_with_workspace_conflict_report():
    workspace = Path(__file__).resolve().parents[2] / "Samples" / "P4G_Steam_Test" / "script_workspace"
    if not workspace.exists():
        return

    project = P4GProject("conflict_mod")
    message = project.message("YOUSUKE_DUNGEON_SEL", speaker="Yosuke")
    message.line("This intentionally collides with an original message name.")

    used_bit = bit(2531, name="P4G_USED_BIT")
    proc = project.procedure("SCR_ONLY_NPC_YOUSUKE")
    with proc.if_date(6, 15, done_bit=used_bit):
        proc.bit_on(used_bit)
        proc.msg(message)

    with TemporaryDirectory() as tmp:
        result = build_project(project, tmp, workspace=workspace)

        assert result.conflict_report is not None
        assert result.conflicts_txt_path is not None and result.conflicts_txt_path.exists()

        kinds = {issue.kind for issue in result.conflict_report.issues}
        assert "bit" in kinds
        assert "procedure-name" in kinds
        assert "message-name" in kinds
        assert "P4GScript Conflict Report" in result.conflicts_txt_path.read_text(encoding="utf-8")


def test_project_build_api_without_cli():
    project = P4GProject("api_mod")
    message = project.message("API_HELLO")
    message.line("Hello from Build API.")
    proc = project.procedure("API_PROC")
    proc.help_msg(message)

    with TemporaryDirectory() as tmp:
        result = project.Build(tmp, compile_bf=False, safety="expert")

        assert result.flow_path.exists()
        assert result.msg_path is not None and result.msg_path.exists()
        assert result.bf_path is None


def test_beginner_safety_blocks_conflicting_project():
    workspace = Path(__file__).resolve().parents[2] / "Samples" / "P4G_Steam_Test" / "script_workspace"
    if not workspace.exists():
        return

    project = P4GProject("blocked_mod", safety="beginner")
    used_bit = bit(2531, name="P4G_USED_BIT")
    proc = project.procedure("MOD_BLOCKED_TEST")
    proc.bit_on(used_bit)

    with TemporaryDirectory() as tmp:
        result = build_project(project, tmp, workspace=workspace)

        assert result.blocked
        assert result.safety_errors
        assert result.compile_result is None


def test_beginner_safety_allows_reserved_bit_with_workspace():
    workspace = Path(__file__).resolve().parents[2] / "Samples" / "P4G_Steam_Test" / "script_workspace"
    if not workspace.exists():
        return

    project = P4GProject("safe_mod", safety="beginner")
    done = project.reserve_bit("MOD_SAFE_DONE")
    proc = project.procedure("MOD_SAFE_TEST")
    proc.bit_on(done)

    with TemporaryDirectory() as tmp:
        result = build_project(project, tmp, workspace=workspace)

        assert not result.blocked
        assert result.safety_errors == ()
        assert result.conflict_report is not None


def test_cli_beginner_safety_without_workspace_writes_sources():
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        buffer = StringIO()
        with redirect_stdout(buffer):
            status = main(["build", str(_example_project()), "--out", str(tmp_path), "--safety", "beginner"])

        assert status == 0
        assert (tmp_path / "mod_hello.flow").exists()
        assert (tmp_path / "mod_hello.msg").exists()
        assert "Safety blocked build" not in buffer.getvalue()


def test_build_copies_imported_bf_and_records_target():
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        original = tmp_path / "original_comu00.bf"
        original.write_bytes(b"fake-bf")

        project = P4GProject("patch_mod")
        project.target("data_e.cpk/field/script/comu00.bf")
        project.import_bf(original)
        proc = project.soft_hook("SCR_ONLY_NPC_YOUSUKE")
        proc.call_original()

        out_dir = tmp_path / "out"
        result = build_project(project, out_dir)
        manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))

        assert (out_dir / "original_comu00.bf").read_bytes() == b"fake-bf"
        assert result.copied_imports
        assert manifest["target_path"] == "data_e.cpk/field/script/comu00.bf"
        assert manifest["requires_hook"] is True
        assert manifest["imports"][0]["import_path"] == "original_comu00.bf"


def test_manifest_records_create_script_mode():
    project = P4GProject("new_script_mod", create_script=True)
    message = project.message("NEW_SCRIPT_HELLO")
    message.line("Hello from a new script.")
    proc = project.procedure("NEW_SCRIPT_PROC")
    proc.msg(message)

    with TemporaryDirectory() as tmp:
        result = build_project(project, tmp, safety="expert")
        manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))

        assert manifest["create_script"] is True
        assert manifest["build_mode"] == "create"
        assert manifest["requires_hook"] is False


def test_hook_marks_project_as_patch_mode_in_manifest():
    project = P4GProject("patch_mode_mod")
    proc = project.replace_hook("ORIGINAL_PROC")
    proc.call_original()

    with TemporaryDirectory() as tmp:
        result = build_project(project, tmp, safety="expert")
        manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))

        assert project.create_script is False
        assert manifest["create_script"] is False
        assert manifest["build_mode"] == "patch"
        assert manifest["requires_hook"] is True


def test_empty_source_creates_new_script_target():
    from p4gscript import Empty

    project = P4GProject("empty_source_mod", source=Empty(target="data_e.cpk/field/script/custom.bf"))
    proc = project.procedure("CUSTOM_PROC")
    proc.return_()

    with TemporaryDirectory() as tmp:
        result = build_project(project, tmp, safety="expert")
        manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))

        assert project.create_script is True
        assert project.imports == []
        assert manifest["target_path"] == "data_e.cpk/field/script/custom.bf"
        assert manifest["build_mode"] == "create"


def test_bf_source_imports_original_and_sets_patch_mode():
    from p4gscript import BF

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        original = tmp_path / "f007.bf"
        original.write_bytes(b"fake-bf")

        project = P4GProject(
            "bf_source_mod",
            source=BF(original, target="data_e.cpk/field/script/f007.bf"),
        )
        proc = project.replace_hook("select_nanako_okaeri")
        proc.call_original()

        result = build_project(project, tmp_path / "out", safety="expert")
        manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))

        assert project.create_script is False
        assert (tmp_path / "out" / "f007.bf").read_bytes() == b"fake-bf"
        assert manifest["target_path"] == "data_e.cpk/field/script/f007.bf"
        assert manifest["build_mode"] == "patch"

def test_build_api_auto_enables_compiler_hook_for_hook_projects(monkeypatch):
    from p4gscript import BF
    from p4gscript.compiler import CompileResult
    import p4gscript.project as project_module

    captured_hooks: list[bool] = []

    def fake_compile_flow(input_flow, output_bf, config):
        captured_hooks.append(config.hook)
        Path(output_bf).write_bytes(b"compiled-bf")
        return CompileResult(
            command=["AtlusScriptCompiler.exe", "-Compile"],
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(project_module, "compile_flow", fake_compile_flow)

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        original = tmp_path / "original_f007.bf"
        original.write_bytes(b"original-bf")

        project = P4GProject(
            "hook_compile_mod",
            source=BF(original, import_path="original_f007.bf"),
        )
        hook = project.soft_hook("call_lmap")
        hook.call_original()

        result = project.Build(tmp_path / "out", compile_bf=True, safety="expert")

        assert result.bf_path is not None
        assert captured_hooks == [True]


def test_hook_rejects_target_that_would_truncate_suffix_collision():
    import pytest
    from p4gscript.exceptions import RenderError

    project = P4GProject("bad_hook_name_mod")

    with pytest.raises(RenderError, match="too long"):
        project.replace_hook("SCR_BIKE_INVITE_YOUSUKE")
