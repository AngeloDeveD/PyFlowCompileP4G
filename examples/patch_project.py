from __future__ import annotations

from pathlib import Path

from p4gscript import P4GProject


# Оригинальный comu00.bf должен лежать рядом с этим Python-файлом.
# В репозитории .bf-файлы игнорируются, поэтому пользователь берёт файл из игры
# или из своего decompile/workspace и кладёт его в examples/comu00.bf локально.
ORIGINAL_BF = Path(__file__).with_name("comu00.bf")


def build_project() -> P4GProject:
    # patch_field_script сам выставляет target path:
    # data_e.cpk/field/script/comu00.bf
    project = P4GProject.patch_field_script(
        "patch_comu00",
        "comu00",
        ORIGINAL_BF,
        import_path="original_comu00.bf",
        encoding="P4G_EFIGS",
        safety="standard",
    )

    message = project.message("MOD_COMU00_HOOK_HELLO", speaker="Yosuke")
    message.line("This line was injected from Python before the original procedure continues.")

    hook = project.soft_hook("SCR_ONLY_NPC_YOUSUKE")
    hook.say(message)
    hook.call_original()

    return project


if __name__ == "__main__":
    result = build_project().Build()
    print(f"Wrote {result.flow_path}")
    if result.msg_path:
        print(f"Wrote {result.msg_path}")
    if result.bf_path:
        print(f"Wrote {result.bf_path}")