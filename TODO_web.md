# TODO: p4gscript-academy Documentation Roadmap

Этот файл больше не является историческим списком всех идей. Он фиксирует актуальный план документации под текущую структуру проекта `p4gscript` и отделяет обязательное для версии 1.0 от задач, которые можно оставить на потом.

## Главный вывод

Не нужно реализовывать всё, что было в старом `TODO_web.md`.

Старый план был полезен как черновой аудит, но сейчас часть пунктов уже выполнена, часть устарела после изменений API, а часть слишком широка для версии 1.0. Для 1.0 важнее три вещи:

- новичок должен собрать первый рабочий patch-мод без поиска скрытой информации;
- reference должен покрывать публичный API библиотеки, который реально экспортируется из `p4gscript`;
- документация должна честно объяснять reachability: успешная сборка `.bf` не означает, что игра вызовет твой код.

---

## 1. Текущая структура документации

- [x] `docs/p4gscript-academy/index.html` - основной учебный маршрут.
- [x] `docs/p4gscript-academy/reference.html` - отдельный справочник API.
- [x] `docs/p4gscript-academy/app.js` - интерактивная база функций, классов, helpers и diagnostics.
- [x] `docs/p4gscript-academy/styles.css` - оформление academy/reference страниц.
- [x] `examples/nanako_evening_follow_along.py` - beginner follow-along пример.
- [x] `tests/test_rendering.py` - один файл с rendering tests для сообщений, тегов имени, переносов и auto-wrap.

---

## 2. Что уже закрыто

### 2.1 Обучение и mental model

- [x] Объяснить цепочку `Python -> .flow/.msg -> .bf -> Reloaded II -> игра вызывает hook`.
- [x] Разделить build success и реальный in-game trigger.
- [x] Объяснить, что `Empty(...)` / create mode не даёт автозапуск сам по себе.
- [x] Объяснить, что `BF(...)` / patch mode нужен для вмешательства в существующую игровую процедуру.
- [x] Объяснить `replace_hook(...)`, `call_original()` и `*_unhooked()` на уровне beginner tutorial.
- [x] Добавить предупреждение, что `select_nanako_okaeri` не равен любому разговору с Нанако.

### 2.2 MessageScript usability

- [x] `first_name()`, `last_name()`, `msg_var(...)` экспортированы из публичного API.
- [x] `[fName]`, `[lName]`, `[var N]` сохраняются как безопасные inline-теги без ручного `escape=False`.
- [x] Обычный Python `\n` внутри `message.line(...)`, `proc.say(...)` и `proc.help(...)` превращается в `[n]`.
- [x] `line_break()` и `new_line()` экспортированы из публичного API.
- [x] Добавлен auto-wrap: `wrap_width=40`, `max_lines=3`, `auto_wrap=True` по умолчанию.
- [x] `first_name()`, `last_name()` и `msg_var(...)` считаются как 8 видимых символов при auto-wrap.
- [x] Если после переноса больше трёх строк, создаётся следующая `[s]...[w][e]` страница.
- [x] В `src/p4gscript/msg.py` добавлен комментарий про 40 символов, 3 строки и перенос на страницу.

### 2.3 Reference coverage

- [x] В `reference.html` есть статичные таблицы, чтобы страница не была пустой без JS.
- [x] В `app.js` есть интерактивный каталог API с категориями `Project`, `Hooks`, `Messages`, `Expressions`, `Enums`, `Diagnostics`.
- [x] Reference обновлён под текущие helpers: `line_break()`, `new_line()`, `auto_wrap`, `wrap_width`, `max_lines`.
- [x] Reference обновлён под текущие source helpers: `FieldBF`, `FieldEmpty`, `EventBF`, `EventEmpty`, `field_target`, `event_target`.
- [x] Reference обновлён под build/compiler helpers: `build_project`, `build_project_file`, `load_project_from_file`, `CompilerConfig`, `bundled_compiler_path`, `bundled_compiler_root`, `resolve_compiler_path`.
- [x] Reference обновлён под diagnostics: `WorkspaceAnalyzer`, `run_doctor`, `analyze_project_conflicts`, conflict report objects.

---

## 3. Обязательное перед версией 1.0

### 3.1 Проверка примеров

- [ ] Пройти `examples/` и отметить каждый пример одним статусом:
  - `beginner copy-paste`;
  - `standard example`;
  - `patch example requiring original .bf`;
  - `diagnostic / research example`;
  - `legacy / keep but do not teach first`.
- [ ] Убедиться, что первый tutorial не ссылается на нестабильные или исследовательские примеры.
- [ ] Для каждого tutorial-примера указать точный игровой сценарий проверки.

### 3.2 Согласованность API и reference

- [x] Сверить `p4gscript.__all__` с `docs/p4gscript-academy/app.js`.
- [x] Добавить missing public API cards в интерактивный reference.
- [x] Добавить недостающие строки в статичный `reference.html`.
- [ ] Добавить lightweight script/check, который сравнивает `p4gscript.__all__` с reference coverage и печатает пропуски.
- [ ] Решить, какие low-level classes должны быть documented fully, а какие достаточно отметить как advanced/tooling.

### 3.3 Честность про working examples

- [ ] В tutorial явно закрепить формулировку: “пример рабочий при соблюдении условий”, а не “1000% всегда работает”.
- [ ] Для hook-примеров перечислить:
  - какой `.bf` патчится;
  - какая procedure hook target;
  - где в игре она вызывается;
  - что должно быть установлено в Reloaded II;
  - что может помешать срабатыванию.

### 3.4 Диагностика

- [ ] Добавить короткий lesson “Compiled successfully, but nothing happens”.
- [ ] Добавить flowchart диагностики:
  `BF лежит в правильном target? -> Reloaded II видит mod? -> hook target существует? -> игра вызывает target? -> нет конфликта с другим mod?`.
- [ ] Показать, как использовать `HELP_MSG` как временный proof-of-hook.

---

## 4. Не обязательно для 1.0

Эти пункты полезны, но не должны блокировать первую стабильную версию документации.

- [ ] Полный учебник по поиску procedure через все decompiled scripts.
- [ ] Подробная база всех native FlowScript-функций AtlusScriptTools.
- [ ] Большая галерея “что можно сделать в P4G” по модам других авторов.
- [ ] Автоматическая генерация reference.html из docstrings.
- [ ] Интерактивный playground для `.flow/.msg` внутри сайта.
- [ ] Отдельный раздел по C# Reloaded-II runtime mods и input hooks.

---

## 5. Что не добавлять сейчас

- [ ] Не обещать автозапуск create-mode script без внешнего caller.
- [ ] Не делать beginner-уроки на raw native calls вроде `STOP_BGM`, пока не объяснён `safety="standard"`.
- [ ] Не вставлять примеры, которые “компилируются”, но не имеют понятного in-game trigger.
- [ ] Не превращать главный tutorial в полный API dump. Для этого есть `reference.html`.
- [ ] Не документировать внутренние private helpers как пользовательский API.

---

## 6. Reference coverage checklist

### Project / Source

- [x] `P4GProject`
- [x] `P4GProject.new_script(...)`
- [x] `P4GProject.patch_script(...)`
- [x] `P4GProject.new_field_script(...)`
- [x] `P4GProject.patch_field_script(...)`
- [x] `P4GProject.new_event_script(...)`
- [x] `P4GProject.patch_event_script(...)`
- [x] `BF(...)`, `Empty(...)`
- [x] `FieldBF(...)`, `FieldEmpty(...)`
- [x] `EventBF(...)`, `EventEmpty(...)`
- [x] `field_target(...)`, `event_target(...)`
- [x] `project.target(...)`, `project.use(...)`
- [x] `project.import_bf(...)`, `project.import_flow(...)`, `project.import_msg(...)`
- [x] `project.write(...)`, `project.compile(...)`, `project.build(...)`, `project.Build(...)`
- [x] `project.render_flow()`, `project.render_msg()`

### Hooks / Procedure

- [x] `project.replace_hook(...)`, `project.soft_hook(...)`, `project.after_hook(...)`
- [x] `project.show_message_before_original(...)`
- [x] `project.replace_with_message(...)`
- [x] `project.show_help_once(...)`
- [x] `proc.say(...)`, `proc.help(...)`, `proc.ask(...)`, `proc.ask_yes_no(...)`
- [x] `proc.once(...)`, `proc.during(...)`, `proc.when_time(...)`, `proc.when_bit_clear(...)`, `proc.when_bit_set(...)`
- [x] `proc.bit_on(...)`, `proc.bit_off(...)`, `proc.setBit(...)`, `proc.clearBit(...)`
- [x] `proc.add_yen(...)`, `proc.set_item(...)`, `proc.get_item(...)`, `proc.set_msg_var(...)`
- [x] `proc.call(...)`, `proc.assign_call(...)`, `proc.emit(...)`, `proc.raw(...)`, `proc.line(...)`
- [x] `proc.call_event(...)`, `proc.call_field(...)`, `proc.call_original(...)`, `proc.return_()`
- [x] `proc.open_msg()`, `proc.close_msg()`, `proc.msg(...)`, `proc.help_msg(...)`, `proc.titled_help_msg(...)`

### Messages

- [x] `project.message(...)`, `Message.line(...)`, `Message.raw_line(...)`
- [x] `project.selection(...)`, `Selection.option(...)`
- [x] `first_name()`, `last_name()`, `msg_var(...)`
- [x] `line_break()`, `new_line()`
- [x] `auto_wrap`, `wrap_width`, `max_lines`

### Expressions

- [x] `var(...)`, `rawExpr(...)`, `callExpr(...)`
- [x] `bitChk(...)`, `bitOn(...)`, `bitOff(...)`
- [x] `dateChk(...)`, `checkTimeSpan(...)`, `timeOfDay()`, `getTimeOfDay()`
- [x] `getCnt(...)`, `setCnt(...)`, `getItem(...)`, `setItem(...)`, `addYen(...)`
- [x] `setMsgVar(...)`, `socialStatLevel(...)`
- [x] `openMsg()`, `closeMsg()`, `msg(...)`, `helpMsg(...)`, `titledHelpMsg(...)`
- [x] `callEvent(...)`, `callField(...)`

### Domain / IDs

- [x] `Speaker`, `SpeakerName`
- [x] `Character`, `CharacterProfile`
- [x] `TimeOfDay`, `SocialStat`, `FlowEnumValue`
- [x] `BitId`, `bit(...)`, `EventId`, `FieldId`
- [x] `Bustup`, `VoiceCue`
- [x] `BEGINNER`, `STANDARD`, `EXPERT`, `normalize_safety(...)`

### Build / Diagnostics

- [x] `build_project(...)`, `build_project_file(...)`, `load_project_from_file(...)`
- [x] `BuildResult`, `CompileResult`, `CompilerConfig`
- [x] `bundled_compiler_path()`, `bundled_compiler_root()`, `resolve_compiler_path(...)`
- [x] `WorkspaceAnalyzer`
- [x] `run_doctor(...)`, `DoctorReport`, `DoctorCheck`
- [x] `analyze_project_conflicts(...)`, `ConflictReport`, `ConflictIssue`, `ConflictReference`

---

## 7. Verification commands

Запускать после заметных изменений документации или reference-базы:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -c "from pathlib import Path; import ast; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in Path('src').rglob('*.py')]; print('src ast ok')"
python -B -c "from html.parser import HTMLParser; from pathlib import Path; [HTMLParser().feed(p.read_text(encoding='utf-8')) for p in [Path('docs/p4gscript-academy/index.html'), Path('docs/p4gscript-academy/reference.html')]]; print('html ok')"
node --check docs/p4gscript-academy/app.js
```

Rendering tests можно запускать без `pytest` так:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -c "from pathlib import Path; path=Path('tests/test_rendering.py').resolve(); ns={'__file__': str(path), '__name__': 'manual'}; exec(path.read_text(encoding='utf-8-sig'), ns); count=0
for name, func in sorted(ns.items()):
    if name.startswith('test_') and callable(func):
        func(); count += 1
print(f'test_rendering functions ok: {count}')"
```