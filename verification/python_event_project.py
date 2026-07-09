from __future__ import annotations

from p4gscript import Bustup, P4GProject, VoiceCue, var


def build_project() -> P4GProject:
    project = P4GProject("python_event", encoding="P4G_EFIGS", safety="beginner")

    done = project.reserve_bit(
        "MOD_VERIFY_DONE",
        reason="prevents repeated verification event",
        range_start=9000,
        range_end=9000,
    )

    hello = project.message("MOD_VERIFY_HELLO", speaker="Yosuke")
    hello.line(
        "Python SDK verification message.",
        bustup=Bustup(character_id=2, expression_id=1, costume_id=65535, position=1),
        voice=VoiceCue(event_major=3, event_minor=0, event_sub=6, cue_id=202),
    )

    yes = project.message("MOD_VERIFY_YES", speaker="Yosuke")
    yes.line("Choice 0 was selected.")

    no = project.message("MOD_VERIFY_NO", speaker="Yosuke")
    no.line("Another choice was selected.")

    choice = project.selection("MOD_VERIFY_CHOICE")
    choice.option("Yes").option("No")

    proc = project.procedure("MOD_VERIFY_EVENT")
    with proc.if_date(6, 15, done_bit=done):
        proc.open_msg()
        proc.msg(hello)
        proc.sel("choice", choice)
        with proc.if_(var("choice") == 0):
            proc.msg(yes)
        with proc.if_(var("choice") != 0):
            proc.msg(no)
        proc.close_msg()
        proc.bit_on(done)

    return project
