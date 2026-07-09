# P4GScript SDK Roadmap

Этот план описывает, как развивать Python-библиотеку для Persona 4 Golden так,
чтобы ей было удобно пользоваться и новичку, и опытному моддеру.

## Главная идея

Библиотека не должна прятать Atlus scripting полностью. Она должна дать два слоя:

```text
High-level API
  Для новичков: "покажи сообщение", "сделай выбор", "событие на дату".

Low-level API
  Для опытных: raw native calls, raw message tags, hooks, ids, ручной контроль.
```

Оба слоя должны генерировать обычные `.flow` и `.msg`, чтобы результат можно было
проверить, отредактировать руками и собрать через `AtlusScriptCompiler`.

## Фаза 0. Текущий MVP

Уже заложено:

- `P4GProject`
- `Message`
- `Selection`
- `Procedure`
- `BitId`
- `EventId`
- `FieldId`
- `Bustup`
- `VoiceCue`
- генерация `.msg`
- генерация `.flow`
- compile wrapper для `AtlusScriptCompiler`
- warning для unsafe bits

Цель MVP:

```text
Python code -> generated .flow/.msg -> AtlusScriptCompiler -> .bf
```

## Фаза 1. Удобные сценарии для новичков

Нужно добавить recipes:

- `show_message(...)`
- `ask_choice(...)`
- `on_date(...)`
- `once(bit=...)`
- `give_item(...)`
- `call_event(...)`
- `go_to_field(...)`
- `start_dungeon(...)`

Пример будущего API:

```python
event = project.on_date(6, 15, once=BitId(9000, name="MOD_EVENT_DONE"))
event.show_message("MOD_HELLO", speaker="Yosuke", text="Yo, want to go inside the TV?")
```

Что должен получить пользователь:

```text
Понятный Python-код.
Сгенерированный .flow.
Сгенерированный .msg.
Предупреждения о bit/count/event IDs.
```

## Фаза 2. Expert API

Опытный моддер должен иметь полный контроль:

- `proc.call("FUNCTION_00BA", 0)`
- `proc.raw("...")`
- `message.raw_line("...")`
- raw `[f ...]` tags
- dynamic `SEL(var)`
- ручные hooks
- `call_original()`
- import original `.bf`

Пример:

```python
hook = project.procedure("cmm_bentou_exec_hook")
hook.call_original()
with hook.if_("DATE_CHK(6, 15) == 1 && BIT_CHK(2531) == 0"):
    hook.open_msg()
    hook.msg("MOD_EVENT")
    hook.close_msg()
    hook.call("BIT_ON", 2531)
```

## Фаза 3. Analyzer

Analyzer должен читать decompiled workspace:

```text
script_workspace/decompiled
script_workspace/indexes/procedures.tsv
script_workspace/indexes/native_calls.tsv
script_workspace/indexes/message_tags.tsv
```

И строить database:

- files
- imports
- procedures
- messages
- selections
- native calls
- bit usages
- count usages
- event calls
- field calls

Практическая польза:

- найти процедуру по имени;
- найти все `DATE_CHK`;
- найти все `CALL_EVENT(810, ...)`;
- показать, где используется bit;
- показать, какие message IDs есть в `.msg.h`;
- предупредить, что мод трогает занятый bit.

Стартовая реализация уже есть:

- чтение `procedures.tsv`;
- чтение `native_calls.tsv`;
- чтение `message_tags.tsv`;
- чтение `.msg.h`;
- сканирование `import("...")`;
- сканирование `BIT_*`;
- сканирование `GET_CNT/SET_CNT`;
- сканирование `CALL_EVENT`.
- сканирование `MSG/SEL`;
- сканирование `SET_MSG_VAR`;
- сканирование `CALL_FIELD/CALL_FIELD_SAFE`;
- сканирование `CALL_DUNGEON`;
- сканирование `CALL_BATTLE`.
- procedure spans;
- usage graph для конкретной procedure.
- text report для конкретной procedure.
- CLI команды `summary`, `report`, `find-procedure`, `message`, `bit`.
- CLI/API `doctor` для проверки окружения.
- CLI `build` для Python project -> `.flow/.msg/manifest`.
- build manifest `manifest.json` и `manifest.txt`.
- build: подключение workspace/analyzer через `--workspace`.
- build: conflict report по bits/procedures/messages.
- bit registry через `project.reserve_bit(...)`.
- safety modes `beginner`, `standard`, `expert`.
- beginner safety блокирует конфликтную сборку до `.bf` compilation.

Дальше нужно расширить analyzer:

- карта `.flow -> .msg -> .msg.h`;
- report conflicts for generated projects.
- relation graph: procedure -> native calls -> messages -> selections.
- build: configurable conflict policy per issue kind.
- doctor: проверка installable package, версий и build output.

## Фаза 4. Safety modes

Базовые режимы уже есть:

```python
project.safety = "beginner"
project.safety = "expert"
```

Beginner mode:

- требует `--workspace` при build;
- блокирует `.bf` compilation при conflict warnings;
- подсвечивает unsafe raw/manual bits;
- дальше должен запрещать raw calls без `unsafe=True`;
- предупреждает о голых int bits;
- требует reason для custom bits;
- показывает подсказки по encoding;
- не дает случайно собрать `data_e` с `P4G_JP`.

Expert mode:

- разрешает raw operations;
- всё равно пишет manifest использованных IDs;
- не мешает ручной работе.

## Фаза 5. Mod manifest

SDK должен генерировать не только `.flow/.msg`, но и manifest:

```text
Used bits:
  9000 - MOD_EVENT_DONE - prevents repeated date event

Used counts:
  none

Used events:
  CALL_EVENT(810, 2, 0)

Generated files:
  my_mod.flow
  my_mod.msg
  my_mod.bf
```

Это поможет и новичку, и опытному моддеру понимать, что именно делает мод.

## Фаза 6. P4G constants database

Постепенно нужно добавлять понятные aliases:

- characters
- bustup IDs
- Social Link IDs
- common event IDs
- field IDs
- item ranges
- known flags
- known count IDs

Но каждое имя должно быть подтверждено источником:

```text
original script usage
library JSON
community table
manual reverse engineering note
```

## Фаза 7. Установка и интеграция

Позже можно добавить:

- генерацию Aemulus package structure;
- копирование `.bf` в правильный путь;
- `Package.xml`;
- build folder;
- compile logs;
- conflict report.

До этого SDK должен честно говорить:

```text
Я сгенерировал .bf.
Установка в игру - отдельный шаг.
```

## Первые задачи разработки

1. Довести MVP генерации `.flow/.msg`.
2. Добавить tests для render output.
3. Добавить analyzer для `.msg.h`.
4. Добавить analyzer для `procedures.tsv`.
5. Добавить high-level `show_message`.
6. Добавить high-level `date_event`.
7. Добавить manifest генератор.
8. Добавить compile logs.
