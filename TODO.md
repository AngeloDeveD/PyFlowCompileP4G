# TODO: p4gscript SDK Roadmap

Рабочий план внедрения beginner/standard API и P4G helpers.
Файл нужно обновлять по мере выполнения задач и дополнять новыми идеями.

## Принципы

- [x] `beginner` - безопасный режим для новичков: готовые helpers, P4G domain objects, минимум raw FlowScript.
- [x] `standard` - расширенный режим: все возможности `beginner` плюс raw conditions, direct native calls и редкие функции.
- [x] Код, написанный в beginner-стиле, должен работать в `standard`.
- [x] Hook должен мыслиться как `source BF + target path + procedure name`, потому что имена процедур часто повторяются в разных `.bf`.
- [x] Для английских P4G-модов дефолтно ориентироваться на `data_e.cpk` и `P4G_EFIGS`.
- [x] Пользователь не должен вручную управлять `.msg.h`; SDK генерирует `.msg`, `.flow` импортирует `.msg`, compiler связывает имена.

## 1. Safety Model

- [x] Нормализовать значения `safety`: `beginner`, `standard`.
- [x] Добавить алиасы для частых опечаток: `begginer -> beginner`, `standart -> standard`.
- [x] Зафиксировать порядок возможностей: `standard` включает `beginner`.
- [x] В `beginner` ограничить raw `.flow` строки там, где есть безопасный helper.
- [x] В `standard` оставить raw `.if_("...")`, direct calls и advanced/native usage.
- [x] Добавить понятные ошибки, если beginner-пользователь вызывает advanced API.
- [x] Оставить `expert` как legacy/internal режим для существующих тестов и обхода conflict checks.

## 2. Expression DSL

- [x] Добавить базовые expression objects: `Expr`, `CallExpr`, `BinaryExpr`, `ValueExpr`.
- [x] Поддержать сравнения: `==`, `!=`, `<`, `>`, `<=`, `>=`.
- [x] Поддержать логические операции через безопасный синтаксис: `&` и `|`.
- [x] Сделать рендер выражений в валидный `.flow`.
- [x] Поддержать форму:

```python
with proc.if_(bitChk(MOD_HELLO_DONE) == 0):
    ...
```

- [x] Не обещать обычный Python `if checkTimeSpan(...):`, потому что Python выполнит условие сразу, а не сгенерирует `.flow`.
- [x] Добавить `var("choice")` для beginner-safe локальных переменных вместо raw строки `"choice == 0"`.

## 3. Beginner Helpers

- [x] `bitChk(bit_id)`
- [x] `bitOn(bit_id)`
- [x] `bitOff(bit_id)`
- [x] `getCnt(index)`
- [x] `setCnt(index, value)`
- [x] `dateChk(month, day)`
- [x] `checkTimeSpan(start_month, start_day, end_month, end_day)`
- [x] `timeOfDay()` / `getTimeOfDay()`
- [x] `callEvent(major, minor, sub=0)` and `callEvent(EventId(...))`
- [x] `callField(field_major, field_minor, location=0, weather=0)` and `callField(FieldId(...))`
- [ ] `msg(message)` как top-level helper: пока не экспортирован, чтобы не конфликтовать с модулем `p4gscript.msg`; есть `proc.msg(message)`.
- [x] `helpMsg(message)`
- [x] `socialStatLevel(stat)`
- [x] `openMsg()`
- [x] `closeMsg()`

## 4. P4G Domain Objects

- [x] Добавить полный `Speaker` / `NPC` список для частых data_e speakers:
  `Var 0 (главный герой) - MainCharacter`, `Nanako`, `Dojima`, `Yosuke`, `Chie`, `Teddie`, `Yukiko`, `Kanji`, `Rise`, `Naoto`, `Marie`, `Adachi`, `Margaret`, `Igor`, `Ai`, `Aika`, `Ayane`, `Daisuke`, `Eri`, `Fox`, `Hanako`, `Hisano`, `Morooka`, `Kou`, `Mayumi`, `Misuzu`, `Mitsuo`, `GasStation`, `Edogawa`, `Naoki`, `Kashiwagi`, `Shiroku`, `Tanaka`, `Saki`, `Sayoko`, `Shu`, `Namatame`, `Yumi`, `Yuuta`
- [x] Добавить базовый `Speaker` для главных персонажей и нескольких частых NPC.
- [x] Добавить `TimeOfDay`:
  `LATE_NIGHT = 0`, `UNKNOWN_1 = 1`, `UNKNOWN_2 = 2`, `SCHOOL = 3`, `DAY = 4`, `EVENING = 5`.
- [x] Добавить `SocialStat`:
  `COURAGE`, `KNOWLEDGE`, `DILIGENCE`, `UNDERSTANDING`, `EXPRESSION`.
- [ ] Добавить wrappers для часто используемых Social Link helpers позже, после field helpers.

## 5. Procedure API

- [x] `proc.if_(Expr)` должен принимать DSL expressions.
- [x] В `standard` `proc.if_(str)` остается доступным.
- [x] В `beginner` `proc.if_(str)` запрещен с понятной ошибкой.
- [x] Добавить удобные aliases в Python-стиле и P4G-стиле, если это не раздует API: `setBit`, `clearBit`, `callOriginal`.
- [x] Проверить совместимость старых методов `open_msg`, `msg`, `close_msg`, `help_msg`, `call_original`.
- [x] Добавить `proc.help(...)` как отдельный beginner-friendly shortcut.
- [x] Beginner-friendly методы сейчас: `proc.say(...)`, `proc.setBit(...)`, `proc.clearBit(...)`, `proc.callOriginal()`.

## 6. Hook API

- [x] Сохранить разделение `BF(...)` и `Empty(...)`.
- [x] Patch mode: если пользователь hook'ает существующую процедуру, нужен `BF(...)`.
- [x] Create mode: если создается новый скрипт, нужен `Empty(...)`.
- [x] В manifest явно писать `create_script` / `patch`.
- [x] Добавить helpers для типовых hook-сценариев:
  "показать сообщение перед оригиналом",
  "заменить поведение",
  "показать help один раз".
- [x] Не скрывать полностью факт patch/create: пользователь должен понимать, что он собирает.

## 7. Examples

- [x] Переписать `examples/f007_nanako_greeting.py` в beginner-style.
- [x] Переписать `examples/f007_save_from_action.py` в mixed style: raw native calls оставлены в `standard`.
- [x] Оставить raw/advanced вариант как `standard` example.
- [x] Убрать из новых примеров `P4GSCRIPT_WORKSPACE` там, где можно без потери удобства.
- [x] Использовать `BF(...)` / `Empty(...)` вместо ручного `import_bf(...)` во всех новых примерах.
- [x] Показать `Build(Debug=False)` и `Build(Debug=True)`.

## 8. Tests

Все новые тесты для этой работы должны лежать в одном файле:

```text
tests/test_safety_dsl_integration.py
```

- [x] Проверить, что `beginner` принимает helpers.
- [x] Проверить, что `standard` принимает helpers из `beginner`.
- [x] Проверить, что `standard` принимает raw string conditions.
- [x] Проверить поведение `beginner` при raw string conditions.
- [x] Проверить рендер `bitChk(...) == 0` -> `BIT_CHK(...) == 0`.
- [x] Проверить рендер `checkTimeSpan(...) == 1` -> `CHECK_TIME_SPAN(...) == 1`.
- [x] Проверить `timeOfDay() == TimeOfDay.EVENING`.
- [x] Проверить `Speaker.NANAKO` в generated `.msg`.
- [x] Проверить `BF(...)` -> patch mode manifest.
- [x] Проверить `Empty(...)` -> create mode manifest.
- [x] Проверить минимальную сборку `.bf` через bundled `AtlusScriptCompiler`, если compiler доступен.

## 9. Test Artifact Cleanup

- [x] Все тесты должны писать исходники и `.bf` только во временную папку.
- [x] После теста должны удаляться `.bf`, `.flow`, `.msg`, `.msg.h`, `manifest.json`, `manifest.txt`, `conflicts.txt`.
- [x] Тесты не должны оставлять файлы в `examples/build` или в корне проекта.
- [x] Если используется `TemporaryDirectory`, дополнительно проверить, что временная папка исчезает после завершения.

## 10. Final Validation

- [x] Запустить `python -m compileall -q src examples tests verification`.
- [x] Запустить `tests/test_safety_dsl_integration.py`.
- [x] Если `pytest` недоступен, тестовый файл должен запускаться через `unittest` или обычный `python tests/test_safety_dsl_integration.py`.
- [x] Проверить, что key examples still build без `.bf` compilation: `f007_nanako_greeting`, `mod_project`.
- [x] Проверить, что compiler debug output читаемый при `Build(Debug=True)`.


## 11. Public API Documentation

- [x] Добавить подробные docstring-комментарии к публичному expression DSL API.
- [x] Добавить подробные docstring-комментарии к Procedure API.
- [x] Добавить подробные docstring-комментарии к P4GProject build/source API.
- [x] Добавить подробные docstring-комментарии к BF(...) / Empty(...).
- [x] Добавить подробные docstring-комментарии к Speaker / TimeOfDay.
- [x] Добавить подробные docstring-комментарии к MessageScript helpers.
- [x] Добавить подробные docstring-комментарии к ID helpers: bit, EventId, FieldId, Bustup, VoiceCue.
- [ ] При добавлении нового публичного API сразу писать docstring с описанием действия, параметров и safety-ограничений.

## Progress Log

### 2026-07-07

- Продолжение по TODO:
  - расширен `Speaker` до полного списка из TODO;
  - добавлены `FlowEnumValue` и `SocialStat` с рендером `SocialStat.Courage` и аналогичных FlowScript enum values;
  - добавлен beginner helper `socialStatLevel(stat)` для `GET_SOCIAL_STAT_LEVEL(stat)`;
  - добавлен `proc.help(...)` для автоматического создания help-message блока;
  - добавлены hook helpers: `show_message_before_original(...)`, `replace_with_message(...)`, `show_help_once(...)`;
  - примеры `patch_project.py`, `p4g_hello_world_mod.py`, `f007_save_from_action.py`, `f007_test_mode_dialog.py`, validation часть FEmulator builder переведены на `BF(...)`;
  - `p4g_hello_world_mod.py` переведен с raw beginner condition на `bitChk(...) == 0`;
  - FEmulator builder переведен в `standard`, потому что использует raw `FLD_FUNCTION_0000()` conditions;
  - README minimal example переведен на `bitChk(done) == 0`;
  - `beginner` build больше не требует workspace: workspace нужен только для optional conflict analysis, если пользователь сам передал путь;
  - `examples/f007_save_from_action.py`, `examples/f007_test_mode_dialog.py` и `docs/P4GScriptGuide.html` убраны от `P4GSCRIPT_WORKSPACE`;
  - docs examples переведены с ручного `target/import_bf` на `BF(...)` / `Empty(...)`;`r`n  - в guide явно указано, что `Empty(...)` собирает новый скрипт, а для проверки Nanako hook в игре нужен patch-вариант `BF(...)`.
- Проверки после продолжения:
  - `python -m compileall -q src tests examples verification`
  - `python tests/test_safety_dsl_integration.py`
  - custom no-fixture runner: 36 test functions passed
  - compile/debug smoke через bundled `tools/AtlusScriptTools/AtlusScriptCompiler.exe`: PASS
  - render smoke для `patch_project`, `p4g_hello_world_mod`, `f007_save_from_action`, `f007_test_mode_dialog`: PASS
  - `f007_nanako_greeting` compile smoke без `P4GSCRIPT_WORKSPACE`, с `Debug=True`: PASS
  - source write smoke для `f007_save_from_action`, `f007_test_mode_dialog` без `.bf` compilation: PASS
  - собраны game-test пакеты через внешний оригинальный `f007.bf` из AtlusScriptTools sample workspace:
    `build/game_test/f007_test_mode_dialog_package/data_e.cpk/field/script/f007.bf`,
    `build/game_test/f007_save_from_action_package/data_e.cpk/field/script/f007.bf`.
  - создан Reloaded II smoke-test mod project:
    `E:/Reloaded-II/Mods/p4gscript.test_mode_dialog`, runtime files:
    `FEmulator/PAK/field/pack/fd007_001.arc/f007.bf`,
    `FEmulator/PAK/field/pack/fd007_002.arc/f007.bf`.
- Добавлены `safety.py`, `expressions.py`, `domain.py`.
- Исправлен `P4GProject.compile(debug=...)`: убрана ошибочная ссылка на `Debug`.
- `beginner` теперь блокирует `Procedure.raw(...)`, raw string conditions и неизвестные raw native calls.
- `standard` сохраняет raw conditions/direct native calls.
- `verification/python_event_project.py` переведен с raw `choice == 0` на `var("choice") == 0`.
- `verification/verify_python_to_flow_msg.py` больше не падает без внешнего `script_workspace` при golden render check.
- Проверки:
  - `python -m compileall -q src tests examples verification`
  - `python tests/test_safety_dsl_integration.py`
  - custom no-fixture runner: 33 test functions passed
  - `f007_nanako_greeting` smoke build without `.bf` compilation
  - `mod_project` smoke build without `.bf` compilation
- `python -m pytest ...` не запускался полноценно: в текущем окружении нет установленного `pytest`.

## Notes From Decompiled P4G Workspace

- `data_e.cpk` содержит 490 `.flow`, все имеют пару в `data.cpk`.
- Самые частые native-вызовы: `BIT_ON`, `MSG`, `BIT_CHK`, `GET_SL_LEVEL`, `CLOSE_MSG_WIN`, `CHECK_TIME_SPAN`, `OPEN_MSG_WIN`, `CALL_EVENT`, `BIT_OFF`, `SET_CNT`, `GET_CNT`, `SEL`, `DATE_CHK`.
- Field scripts чаще используют `MSG`, `SEL`, `BIT_CHK`, `CHECK_TIME_SPAN`, `CALL_EVENT`, `GET_TIME_OF_DAY`, `CALL_FIELD`, `HELP_MSG`.
- Event scripts чаще используют social-link/status functions и `EVT_FUNCTION_*`.
- Scheduler - отдельный будущий слой, его не смешивать с первым beginner field-hook API.