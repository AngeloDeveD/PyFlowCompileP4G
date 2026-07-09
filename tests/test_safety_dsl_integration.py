import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

SDK_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SDK_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from p4gscript import (
    BF,
    Empty,
    FieldBF,
    FieldEmpty,
    P4GProject,
    SocialStat,
    Speaker,
    TimeOfDay,
    bitChk,
    build_project,
    bundled_compiler_path,
    callExpr,
    checkTimeSpan,
    event_target,
    field_target,
    getItem,
    rawExpr,
    socialStatLevel,
    timeOfDay,
    var,
)
from p4gscript.exceptions import SafetyError


def _assert_raises(exc_type, action):
    try:
        action()
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__}")


def test_beginner_dsl_renders_without_leaking_generated_sources():
    temp_root = None
    with TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        project = P4GProject(
            "dsl_beginner_mod",
            source=Empty(target="data_e.cpk/field/script/dsl_beginner_mod.bf"),
            safety="begginer",
        )
        done = project.reserve_bit("MOD_DSL_DONE")

        proc = project.procedure("MOD_DSL_PROC")
        condition = (
            (checkTimeSpan(4, 1, 5, 6) == 1)
            & (bitChk(done) == 0)
            & (timeOfDay() == TimeOfDay.EVENING)
        )
        with proc.if_(condition):
            proc.say(Speaker.NANAKO, "Good morning!")
            proc.setBit(done)

        result = build_project(project, temp_root / "out", compile_bf=False, safety="standart")
        manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))
        flow = result.flow_path.read_text(encoding="utf-8")
        msg = result.msg_path.read_text(encoding="utf-8")

        assert project.safety == "beginner"
        assert result.safety == "standard"
        assert "CHECK_TIME_SPAN(4, 1, 5, 6) == 1" in flow
        assert "BIT_CHK(MOD_DSL_DONE) == 0" in flow
        assert "GET_TIME_OF_DAY() == 5" in flow
        assert "BIT_ON(MOD_DSL_DONE);" in flow
        assert "[msg MOD_DSL_PROC_MSG_1 [Nanako]]" in msg
        assert manifest["build_mode"] == "create"
        assert manifest["safety"]["mode"] == "standard"
        assert list(temp_root.rglob("*.flow"))
        assert list(temp_root.rglob("*.msg"))
        assert result.bf_path is None

    assert temp_root is not None and not temp_root.exists()


def test_beginner_blocks_raw_api_and_standard_allows_it():
    project = P4GProject("raw_blocked", safety="beginner")
    proc = project.procedure("RAW_BLOCKED_PROC")

    _assert_raises(SafetyError, lambda: proc.raw("SAVE_ASK(3);"))
    _assert_raises(SafetyError, lambda: proc.call("SAVE_ASK", 3))
    _assert_raises(SafetyError, lambda: proc.if_("BIT_CHK(9000) == 0"))
    _assert_raises(SafetyError, lambda: proc.if_(rawExpr("BIT_CHK(9000) == 0")))
    _assert_raises(SafetyError, lambda: proc.if_(callExpr("SAVE_ASK", 3) == 1))
    with proc.if_(var("choice") == 0):
        proc.open_msg()

    beginner_flow = project.render_flow()
    assert "choice == 0" in beginner_flow

    standard_project = P4GProject("raw_allowed", safety="standart")
    standard_proc = standard_project.procedure("RAW_ALLOWED_PROC")
    standard_proc.raw("SAVE_ASK(3);")
    with standard_proc.if_("BIT_CHK(9000) == 0"):
        standard_proc.call("STOP_BGM", 30)

    flow = standard_project.render_flow()
    assert standard_project.safety == "standard"
    assert "SAVE_ASK(3);" in flow
    assert "STOP_BGM(30);" in flow




def test_domain_helpers_and_help_shortcut_render():
    project = P4GProject("domain_helper_mod", safety="beginner")
    proc = project.procedure("DOMAIN_HELPER_PROC")

    with proc.if_(socialStatLevel(SocialStat.COURAGE) >= 3):
        proc.help("Courage check passed.")
        proc.say(Speaker.MAIN_CHARACTER, "I am ready.")

    flow = project.render_flow()
    msg = project.render_msg()

    assert "GET_SOCIAL_STAT_LEVEL(SocialStat.Courage) >= 3" in flow
    assert "HELP_MSG(DOMAIN_HELPER_PROC_MSG_1);" in flow
    assert "MSG(DOMAIN_HELPER_PROC_MSG_2);" in flow
    assert "[msg DOMAIN_HELPER_PROC_MSG_1]" in msg
    assert "Courage check passed." in msg
    assert "[msg DOMAIN_HELPER_PROC_MSG_2 [Var 0]]" in msg
    assert "I am ready." in msg
    assert str(SocialStat.EXPRESSION) == "SocialStat.Expression"
    assert str(Speaker.GAS_STATION) == "GasStation"
    assert str(Speaker.YUUTA) == "Yuuta"



def test_hook_scenario_helpers_render_common_patterns():
    project = P4GProject("hook_helper_mod", safety="beginner")
    done = project.reserve_bit("MOD_HELP_SHOWN")

    project.show_message_before_original("ORIGINAL_TALK", Speaker.NANAKO, "Before original.")
    project.replace_with_message("ORIGINAL_REPLACE", Speaker.YOSUKE, "Replacement behavior.")
    project.show_help_once("ORIGINAL_HELP", "Help once.", done)

    flow = project.render_flow()
    msg = project.render_msg()

    assert project.create_script is False
    assert "void ORIGINAL_TALK_hook()" in flow
    assert "MSG(ORIGINAL_TALK_hook_MSG_1);" in flow
    assert "ORIGINAL_TALK_unhooked();" in flow
    assert "void ORIGINAL_REPLACE_hook()" in flow
    assert "MSG(ORIGINAL_REPLACE_hook_MSG_2);" in flow
    assert "ORIGINAL_REPLACE_unhooked();" not in flow
    assert "void ORIGINAL_HELP_hook()" in flow
    assert "if (BIT_CHK(MOD_HELP_SHOWN) == 0)" in flow
    assert "HELP_MSG(ORIGINAL_HELP_hook_MSG_3);" in flow
    assert "BIT_ON(MOD_HELP_SHOWN);" in flow
    assert "ORIGINAL_HELP_unhooked();" in flow
    assert "const int MOD_HELP_SHOWN = 9000;" in flow
    assert "[msg ORIGINAL_TALK_hook_MSG_1 [Nanako]]" in msg
    assert "Before original." in msg
    assert "[msg ORIGINAL_REPLACE_hook_MSG_2 [Yosuke]]" in msg
    assert "Replacement behavior." in msg
    assert "[msg ORIGINAL_HELP_hook_MSG_3]" in msg
    assert "Help once." in msg



def test_compile_bf_and_debug_output_when_compiler_available():
    compiler = bundled_compiler_path()
    if not compiler.exists():
        return

    temp_root = None
    with TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        project = P4GProject(
            "compile_smoke_mod",
            source=Empty(target="data_e.cpk/field/script/compile_smoke_mod.bf"),
            safety="standard",
        )
        proc = project.procedure("COMPILE_SMOKE_PROC")
        proc.say(Speaker.NANAKO, "Compile smoke test.")

        buffer = StringIO()
        with redirect_stdout(buffer):
            result = project.Build(temp_root / "out", compile_bf=True, Debug=True)
        debug_output = buffer.getvalue()

        assert result.bf_path is not None
        assert result.bf_path.exists()
        assert result.bf_path.stat().st_size > 0
        assert "AtlusScriptCompiler command:" in debug_output
        assert "-Compile" in debug_output
        assert list(temp_root.rglob("*.flow"))
        assert list(temp_root.rglob("*.msg"))
        assert list(temp_root.rglob("*.bf"))

    assert temp_root is not None and not temp_root.exists()

def test_empty_and_bf_sources_keep_artifacts_inside_temporary_directory():
    temp_root = None
    with TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        original = temp_root / "f007.bf"
        original.write_bytes(b"fake-bf")

        create_project = P4GProject(
            "create_source_mod",
            source=Empty(target="data_e.cpk/field/script/create_source_mod.bf"),
        )
        create_project.procedure("CREATE_SOURCE_PROC").return_()
        create_result = build_project(create_project, temp_root / "create", compile_bf=False, safety="expert")
        create_manifest = json.loads(create_result.manifest_json_path.read_text(encoding="utf-8"))

        patch_project = P4GProject(
            "patch_source_mod",
            source=BF(original, import_path="original_f007.bf", target="data_e.cpk/field/script/f007.bf"),
        )
        patch_project.replace_hook("select_nanako_okaeri").callOriginal()
        patch_result = build_project(patch_project, temp_root / "patch", compile_bf=False, safety="expert")
        patch_manifest = json.loads(patch_result.manifest_json_path.read_text(encoding="utf-8"))

        assert create_manifest["build_mode"] == "create"
        assert create_manifest["target_path"] == "data_e.cpk/field/script/create_source_mod.bf"
        assert patch_manifest["build_mode"] == "patch"
        assert patch_manifest["target_path"] == "data_e.cpk/field/script/f007.bf"
        assert (temp_root / "patch" / "original_f007.bf").read_bytes() == b"fake-bf"
        assert list(temp_root.rglob("*.bf"))
        assert list(temp_root.rglob("*.flow"))

    assert temp_root is not None and not temp_root.exists()


def test_short_project_constructors_and_source_shortcuts():
    temp_root = None
    with TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        original = temp_root / "f007.bf"
        original.write_bytes(b"fake-bf")

        project = P4GProject.patch_field_script(
            "field_patch_shortcut",
            "f007",
            original,
            import_path="original_f007.bf",
            safety="beginner",
        )
        project.replace_hook("call_lmap").callOriginal()

        result = build_project(project, temp_root / "out", compile_bf=False, safety="expert")
        manifest = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))

        assert field_target("f007") == "data_e.cpk/field/script/f007.bf"
        assert event_target("E860_074A") == "data_e.cpk/event_data/script/E860_074A.bf"
        assert FieldEmpty("f007").target_path == "data_e.cpk/field/script/f007.bf"
        assert FieldBF("f007", original).target_path == "data_e.cpk/field/script/f007.bf"
        assert manifest["target_path"] == "data_e.cpk/field/script/f007.bf"
        assert (temp_root / "out" / "original_f007.bf").read_bytes() == b"fake-bf"

    assert temp_root is not None and not temp_root.exists()


def test_short_procedure_helpers_render_common_beginner_patterns():
    project = P4GProject.new_field_script("easy_beginner_mod", "easy_beginner_mod", safety="beginner")
    done = project.reserve_bit("MOD_EASY_DONE")

    proc = project.procedure("MOD_EASY_PROC")
    proc.get_item("coffeeCount", 123)
    with proc.once(done, condition=timeOfDay() == TimeOfDay.EVENING):
        proc.say(Speaker.NANAKO, "Short API works.")
        choice = proc.ask("choice", "Take 3000 yen", "Take 1 coffee")
        with proc.if_(choice == 0):
            proc.add_yen(3000)
            proc.set_msg_var(0, 3000)
        with proc.if_(choice == 1):
            proc.set_item(123, 1)
    with proc.when_bit_set(done):
        proc.help("Already claimed.")
    with proc.during(4, 1, 5, 6):
        proc.emit(getItem(123))

    flow = project.render_flow()
    msg = project.render_msg()

    assert "if (BIT_CHK(MOD_EASY_DONE) == 0 && (GET_TIME_OF_DAY() == 5))" in flow
    assert "BIT_ON(MOD_EASY_DONE);" in flow
    assert "int coffeeCount = GET_ITEM(123);" in flow
    assert "int choice = SEL(MOD_EASY_PROC_SEL_1);" in flow
    assert "ADD_YEN(3000);" in flow
    assert "SET_MSG_VAR(0, 3000, 0);" in flow
    assert "SET_ITEM(123, 1);" in flow
    assert "if (BIT_CHK(MOD_EASY_DONE) == 1)" in flow
    assert "if (CHECK_TIME_SPAN(4, 1, 5, 6) == 1)" in flow
    assert "GET_ITEM(123);" in flow
    assert "[sel MOD_EASY_PROC_SEL_1 top]" in msg
    assert "Take 3000 yen" in msg
    assert "Take 1 coffee" in msg
if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("test_safety_dsl_integration: PASS")
