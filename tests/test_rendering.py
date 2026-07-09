from pathlib import Path

from p4gscript import Bustup, Character, P4GProject, Speaker, VoiceCue, WorkspaceAnalyzer, bit, first_name, last_name, line_break, msg_var


def test_message_and_flow_rendering():
    project = P4GProject("mod_test")
    done = bit(9000, name="MOD_DONE", reason="test flag")

    message = project.message("MOD_HELLO", speaker="Yosuke")
    message.line(
        "Hello",
        bustup=Bustup(2, 1),
        voice=VoiceCue(3, 0, 6, 202),
    )

    proc = project.procedure("MOD_TEST")
    with proc.if_date(6, 15, done_bit=done):
        proc.open_msg()
        proc.msg(message)
        proc.close_msg()
        proc.bit_on(done)

    flow = project.render_flow()
    msg = project.render_msg()

    assert 'import("mod_test.msg");' in flow
    assert "const int MOD_DONE = 9000;" in flow
    assert "if (DATE_CHK(6, 15) == 1 && BIT_CHK(MOD_DONE) == 0)" in flow
    assert "MSG(MOD_HELLO);" in flow
    assert "[msg MOD_HELLO [Yosuke]]" in msg
    assert "[vp 3 0 6 202]" in msg
    assert "[bup 2 1 65535 1]" in msg


def test_character_speaker_adds_default_bustup():
    project = P4GProject("mod_character")

    message = project.message("MOD_YOSUKE", speaker=Character.YOSUKE)
    message.line("Partner check.")

    msg = project.render_msg()

    assert "[msg MOD_YOSUKE [Yosuke]]" in msg
    assert "[s][bup 2 1 65535 1]Partner check.[n][w][e]" in msg


def test_procedure_say_with_character_adds_default_bustup():
    project = P4GProject("mod_character_say")
    proc = project.procedure("MOD_CHARACTER_SAY")

    proc.say(Character.YOSUKE, "Partner check.")

    flow = project.render_flow()
    msg = project.render_msg()

    assert "MSG(MOD_CHARACTER_SAY_MSG_1);" in flow
    assert "[msg MOD_CHARACTER_SAY_MSG_1 [Yosuke]]" in msg
    assert "[s][bup 2 1 65535 1]Partner check.[n][w][e]" in msg

def test_character_speaker_can_keep_portrait_with_translated_name():
    project = P4GProject("mod_character_translated")
    yosuke = Character.YOSUKE.with_name("Fsul> %aoanura")

    message = project.message("MOD_YOSUKE_RU", speaker=yosuke)
    message.line("Mpe rabptaft!")

    msg = project.render_msg()

    assert "[msg MOD_YOSUKE_RU [Fsul> %aoanura]]" in msg
    assert "[bup 2 1 65535 1]" in msg




def test_player_name_tags_render_without_manual_escape_override():
    project = P4GProject("mod_player_name")
    proc = project.procedure("MOD_PLAYER_NAME")

    proc.say(
        Speaker.NANAKO,
        f"Hello, {first_name()} {last_name()}. You have {msg_var(0)} yen.",
        wrap_width=80,
    )

    msg = project.render_msg()

    assert "[msg MOD_PLAYER_NAME_MSG_1 [Nanako]]" in msg
    assert "Hello, [fName] [lName]. You have [var 0] yen." in msg
    assert "\\[fName\\]" not in msg


def test_player_name_tags_do_not_make_all_brackets_raw():
    project = P4GProject("mod_player_name_brackets")
    message = project.message("MOD_BRACKETS")

    message.line(f"{first_name()} sees [not_a_tag] and ].")

    msg = project.render_msg()

    assert "[fName] sees \\[not_a_tag\\] and \\]." in msg

def test_dialog_python_newline_renders_as_message_line_break():
    project = P4GProject("mod_line_break")
    message = project.message("MOD_LINE_BREAK")

    message.line("First line.\nSecond line.")

    msg = project.render_msg()

    assert "First line.[n]Second line.[n][w][e]" in msg
    assert "First line.\nSecond line." not in msg


def test_dialog_line_break_helper_renders_as_message_line_break():
    project = P4GProject("mod_line_break_helper")
    message = project.message("MOD_LINE_BREAK_HELPER")

    message.line(f"First line.{line_break()}Second line.")

    msg = project.render_msg()

    assert "First line.[n]Second line.[n][w][e]" in msg
    assert "\\[n\\]" not in msg

def test_dialog_auto_wraps_long_text_at_default_width():
    project = P4GProject("mod_auto_wrap")
    message = project.message("MOD_AUTO_WRAP")

    message.line("aaaaaaaaaa bbbbbbbbbb cccccccccc dddddddddd eeeeeeeeee")

    msg = project.render_msg()

    assert "aaaaaaaaaa bbbbbbbbbb cccccccccc[n]dddddddddd eeeeeeeeee[n][w][e]" in msg


def test_dialog_auto_wrap_counts_player_name_tags_as_eight_chars():
    project = P4GProject("mod_auto_wrap_name")
    message = project.message("MOD_AUTO_WRAP_NAME")

    message.line(f"{first_name()} abc", wrap_width=10)

    msg = project.render_msg()

    assert "[fName][n]abc[n][w][e]" in msg


def test_dialog_auto_wrap_splits_pages_after_max_lines():
    project = P4GProject("mod_auto_wrap_pages")
    message = project.message("MOD_AUTO_WRAP_PAGES")

    message.line("one two three four", wrap_width=5, max_lines=3)

    msg = project.render_msg()

    assert "[s]one[n]two[n]three[n][w][e]\n[s]four[n][w][e]" in msg

def test_selection_rendering():
    project = P4GProject("mod_choice")
    selection = project.selection("MOD_CHOICE")
    selection.option('"Yes"').option('"No"')

    proc = project.procedure("MOD_CHOICE_TEST")
    proc.open_msg()
    proc.sel("choice", selection)
    proc.close_msg()

    flow = project.render_flow()
    msg = project.render_msg()

    assert "int choice = SEL(MOD_CHOICE);" in flow
    assert "[sel MOD_CHOICE top]" in msg
    assert '[s]"Yes"[e]' in msg
    assert '[s]"No"[e]' in msg


def test_reserve_bit_renders_named_constant():
    project = P4GProject("mod_reserved")
    done = project.reserve_bit("MOD_RESERVED_DONE", reason="test reservation")

    proc = project.procedure("MOD_RESERVED_TEST")
    with proc.if_date(6, 15, done_bit=done):
        proc.bit_on(done)

    flow = project.render_flow()

    assert "const int MOD_RESERVED_DONE = 9000;" in flow
    assert "BIT_CHK(MOD_RESERVED_DONE)" in flow
    assert "BIT_ON(MOD_RESERVED_DONE);" in flow


def test_reserve_bit_moves_away_from_workspace_used_bit():
    workspace_path = Path(__file__).resolve().parents[2] / "Samples" / "P4G_Steam_Test" / "script_workspace"
    if not workspace_path.exists():
        return

    workspace = WorkspaceAnalyzer.load(workspace_path)
    project = P4GProject("mod_reserved_workspace")
    done = project.reserve_bit("MOD_RESERVED_DONE", range_start=2531, range_end=2600)

    proc = project.procedure("MOD_RESERVED_WORKSPACE_TEST")
    proc.bit_on(done)

    project.attach_analyzer(workspace)

    assert project.bit_constants["MOD_RESERVED_DONE"] != 2531
    assert project.bit_constants["MOD_RESERVED_DONE"] not in workspace.used_bit_ids()
    assert any("moved from 2531" in warning for warning in project.warnings)


def test_patch_project_import_and_hook_rendering():
    project = P4GProject("patch_mod")
    project.target("data_e.cpk/field/script/comu00.bf")
    project.import_bf("original_comu00.bf")

    message = project.message("MOD_PATCH_HELLO", speaker="Yosuke")
    message.line("Hooked message.")

    proc = project.soft_hook("SCR_ONLY_NPC_YOUSUKE")
    proc.open_msg()
    proc.msg(message)
    proc.close_msg()
    proc.call_original()

    flow = project.render_flow()

    assert 'import("original_comu00.bf");' in flow
    assert 'import("patch_mod.msg");' in flow
    assert "void SCR_ONLY_NPC_YOUSUKE_softhook()" in flow
    assert "SCR_ONLY_NPC_YOUSUKE_unhooked();" in flow
    assert project.requires_hook


def test_when_and_say_helpers_render_message_block():
    from p4gscript import TimeSpan

    project = P4GProject("helper_mod")
    proc = project.procedure("HELPER_PROC")
    with proc.when(TimeSpan(4, 1, 5, 6)):
        proc.say("Nanako", "Good morning!")

    flow = project.render_flow()
    msg = project.render_msg()

    assert "if (CHECK_TIME_SPAN(4, 1, 5, 6) == 1)" in flow
    assert "OPEN_MSG_WIN();" in flow
    assert "MSG(HELPER_PROC_MSG_1);" in flow
    assert "CLOSE_MSG_WIN();" in flow
    assert "[msg HELPER_PROC_MSG_1 [Nanako]]" in msg
    assert "Good morning!" in msg


