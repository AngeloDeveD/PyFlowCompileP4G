from __future__ import annotations

from pathlib import Path

from p4gscript import P4GProject, Speaker, TimeOfDay, first_name, timeOfDay


# Оригинальный f007.bf должен лежать рядом с этим Python-файлом.
# Для примера из репозитория это будет examples/f007.bf.
ORIGINAL_F007_BF = Path(__file__).with_name("f007.bf")


def build_project() -> P4GProject:
    # Создаём patch-проект для домашнего field script f007.
    # Мы не создаём новый неизвестный игре .bf, а берём оригинальный f007.bf и
    # добавляем в него hook. Так игра точно знает, когда загружать этот script.
    project = P4GProject.patch_field_script(
        "nanako_evening_follow_along",
        "f007",
        ORIGINAL_F007_BF,
        import_path="original_f007.bf",
        safety="beginner",
    )

    # Bit работает как маленькая память мода. Пока он выключен, сообщение можно
    # показать. После показа hook.once(...) сам включит этот bit, и блок больше
    # не повторится.
    shown = project.reserve_bit(
        "MOD_NANAKO_EVENING_HELLO_SHOWN",
        reason="show follow-along Nanako hello once in the evening",
    )

    # select_nanako_okaeri - конкретная процедура домашней логики f007.
    # Это не любой разговор с Nanako: игра должна дойти именно до этой процедуры.
    hook = project.replace_hook("select_nanako_okaeri")

    # Всё внутри этого блока выполнится один раз и только вечером.
    # hook.help(...) создаёт HELP_MSG popup, а hook.say(...) создаёт обычное
    # диалоговое окно от имени Nanako. first_name() вставляет тег [fName],
    # а библиотека сохраняет такие безопасные теги автоматически.
    with hook.once(shown, condition=timeOfDay() == TimeOfDay.EVENING):
        hook.help("Hello world!", name="MOD_NANAKO_HELLO_HELP")
        hook.say(
            Speaker.NANAKO,
            f"Hello, {first_name()}. Great script!",
            name="MOD_NANAKO_HELLO_DIALOG",
        )

    # replace_hook(...) не вызывает оригинальный код автоматически.
    # Эта строка возвращает стандартный диалог Nanako после нашего сообщения.
    hook.call_original()
    return project


if __name__ == "__main__":
    result = build_project().Build(Debug=True)
    print(f"Wrote flow: {result.flow_path}")
    if result.msg_path:
        print(f"Wrote msg:  {result.msg_path}")
    if result.bf_path:
        print(f"Wrote bf:   {result.bf_path}")