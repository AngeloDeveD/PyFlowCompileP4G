from p4gscript import Character, P4GProject, VoiceCue


def build_project() -> P4GProject:
    project = P4GProject("mod_hello", encoding="P4G_EFIGS")

    done = project.reserve_bit(
        "MOD_HELLO_DONE",
        reason="Prevents repeated test message",
    )

    message = project.message("MOD_HELLO", speaker=Character.YOSUKE)
    message.line(
        "Hello from a buildable Python project.",
        voice=VoiceCue(3, 0, 6, 202),
    )

    proc = project.procedure("MOD_HELLO_TEST")
    with proc.if_date(6, 15, done_bit=done):
        proc.open_msg()
        proc.msg(message)
        proc.close_msg()
        proc.bit_on(done)

    return project


if __name__ == "__main__":
    result = build_project().Build()
    print(f"Wrote {result.flow_path}")
    if result.msg_path:
        print(f"Wrote {result.msg_path}")
    if result.bf_path:
        print(f"Wrote {result.bf_path}")


