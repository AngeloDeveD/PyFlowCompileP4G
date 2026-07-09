from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory


def test_verification_runner_matches_golden_without_compiler():
    import sys

    verification_dir = Path(__file__).resolve().parents[1] / "verification"
    sys.path.insert(0, str(verification_dir))
    try:
        from verify_python_to_flow_msg import main

        with TemporaryDirectory() as tmp:
            buffer = StringIO()
            with redirect_stdout(buffer):
                status = main(["--out", tmp, "--no-compile"])
    finally:
        sys.path.remove(str(verification_dir))

    output = buffer.getvalue()
    assert status == 0
    assert "PASS python_event.flow matches python_event.flow" in output
    assert "PASS python_event.msg matches python_event.msg" in output


def test_patch_project_matches_golden_and_copies_original():
    import json
    import sys

    sdk_root = Path(__file__).resolve().parents[1]
    examples_dir = sdk_root / "examples"
    golden_dir = sdk_root / "verification" / "golden"
    sys.path.insert(0, str(examples_dir))
    try:
        from p4gscript import build_project
        from patch_project import ORIGINAL_BF, build_project as build_patch_project

        if not ORIGINAL_BF.exists():
            return

        with TemporaryDirectory() as tmp:
            result = build_project(build_patch_project(), tmp, workspace=sdk_root.parent / "Samples" / "P4G_Steam_Test" / "script_workspace")
            flow = result.flow_path.read_text(encoding="utf-8").replace("\r\n", "\n")
            msg = result.msg_path.read_text(encoding="utf-8").replace("\r\n", "\n")
            manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))
    finally:
        sys.path.remove(str(examples_dir))

    assert flow == golden_dir.joinpath("patch_comu00.flow").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert msg == golden_dir.joinpath("patch_comu00.msg").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert result.copied_imports
    assert result.project.requires_hook
    assert manifest["target_path"] == "data_e.cpk/field/script/comu00.bf"
    assert manifest["requires_hook"] is True


def test_patch_project_compiles_and_writes_package():
    import sys

    sdk_root = Path(__file__).resolve().parents[1]
    repo_root = sdk_root.parent
    compiler = repo_root / "Build" / "Release" / "net8.0" / "AtlusScriptCompiler.exe"
    workspace = repo_root / "Samples" / "P4G_Steam_Test" / "script_workspace"
    examples_dir = sdk_root / "examples"
    sys.path.insert(0, str(examples_dir))
    try:
        from p4gscript import build_project
        from patch_project import ORIGINAL_BF, build_project as build_patch_project

        if not compiler.exists() or not ORIGINAL_BF.exists() or not workspace.exists():
            return

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package_dir = tmp_path / "package"
            result = build_project(
                build_patch_project(),
                tmp_path / "build",
                workspace=workspace,
                compile_bf=True,
                compiler_path=compiler,
                package_out=package_dir,
            )

            packaged_bf = package_dir / "data_e.cpk" / "field" / "script" / "comu00.bf"
            assert result.bf_path is not None and result.bf_path.exists()
            assert packaged_bf.exists()
            assert packaged_bf.read_bytes() == result.bf_path.read_bytes()
            assert (package_dir / "p4gscript_install_manifest.json").exists()
    finally:
        sys.path.remove(str(examples_dir))
