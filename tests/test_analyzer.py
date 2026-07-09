from pathlib import Path

from p4gscript import P4GProject, WorkspaceAnalyzer, bit


def test_workspace_analyzer_loads_sample_workspace():
    repo_root = Path(__file__).resolve().parents[2]
    workspace_path = repo_root / "Samples" / "P4G_Steam_Test" / "script_workspace"
    if not workspace_path.exists():
        return

    workspace = WorkspaceAnalyzer.load(workspace_path)
    summary = workspace.summary()

    assert summary["procedures"] > 0
    assert summary["procedure_spans"] == summary["procedures"]
    assert summary["message_ids"] > 0
    assert summary["imports"] == 1553
    assert workspace.native_call("BIT_ON").call_count == 41772
    assert workspace.procedures_named("SCR_ONLY_NPC_YOUSUKE")
    assert workspace.message_ids_named("YOUSUKE_DUNGEON_SEL")
    assert summary["message_calls"] > 0
    assert summary["selection_calls"] > 0
    assert summary["msg_var_usages"] > 0
    assert summary["field_calls"] > 0
    assert summary["dungeon_calls"] > 0
    assert summary["battle_calls"] > 0
    assert workspace.message_calls_named("YOUSUKE_DUNGEON_KIKANGAI")
    assert workspace.selection_calls_named("YOUSUKE_DUNGEON_SEL_2")
    assert workspace.msg_var_usages(0)
    assert workspace.field_calls_by_major(7)
    assert workspace.dungeon_calls_by_id(5)

    usage = workspace.procedure_usages("data_e.cpk/field/script/comu00.flow", "SCR_ONLY_NPC_YOUSUKE")[0]

    assert usage.span.procedure_index == 36
    assert usage.message_calls
    assert usage.selection_calls
    assert usage.bits
    assert usage.event_calls
    assert any(call.name == "YOUSUKE_DUNGEON_SEL_2" for call in usage.selection_calls)

    report = workspace.procedure_report("data_e.cpk/field/script/comu00.flow", "SCR_ONLY_NPC_YOUSUKE")
    assert "Procedure Report" in report
    assert "SCR_ONLY_NPC_YOUSUKE" in report
    assert "Message Calls: 85" in report
    assert "Selection Calls: 4" in report
    assert "YOUSUKE_DUNGEON_SEL_2" in report


def test_project_warns_when_bit_exists_in_workspace():
    repo_root = Path(__file__).resolve().parents[2]
    workspace_path = repo_root / "Samples" / "P4G_Steam_Test" / "script_workspace"
    if not workspace_path.exists():
        return

    workspace = WorkspaceAnalyzer.load(workspace_path)
    project = P4GProject("mod_warn").attach_analyzer(workspace)

    proc = project.procedure("MOD_WARN_TEST")
    proc.bit_on(bit(2531, name="MOD_DONE"))

    assert any("appears in original scripts" in warning for warning in project.warnings)
