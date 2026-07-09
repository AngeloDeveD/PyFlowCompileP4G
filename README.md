# p4gscript Standalone Library

Чистая, отдельная копия нашего Python-проекта для Persona 4 Golden.

Эта папка нужна для того, чтобы работать именно с библиотекой, а не с большой
рабочей директории, где накопились временные сборки, verify-артефакты и пакетные
выгрузки.

## Что входит

- `src/p4gscript/` - сама библиотека;
- `tests/` - тесты;
- `examples/` - живые примеры Python-проектов;
- `verification/` - golden-проверки генерации `.flow/.msg`;
- `docs/` - HTML-документация по P4G-скриптингу;
- `tools/AtlusScriptTools/` - bundled Atlus compiler build;
- `pyproject.toml` - упаковка проекта;
- `LICENSE.txt` - лицензия;
- `ROADMAP.md` - дальнейший план развития.

## Что специально не перенесено

Сюда не копировались большие временные артефакты из старой рабочей директории:

- `build/`;
- `hello_world_*_build/`;
- `hello_world_*_package/`;
- `verification_probe/`;
- `__pycache__/`;
- прочие промежуточные `.bf/.flow/.msg`, собранные для проверки.

Идея простая: в этой папке лежит именно библиотека и минимально нужные материалы
вокруг нее.

## Структура

```text
project-root/
  src/p4gscript/
  tests/
  examples/
  verification/
  docs/
  tools/
  pyproject.toml
  README.md
  ROADMAP.md
  LICENSE.txt
```

## Установка

Из этой папки:

```powershell
py -m pip install -e .
```

Или без установки:

```powershell
$env:PYTHONPATH="src"
py -m p4gscript --help
```

## Bundled compiler

В этой папке библиотека теперь ожидает compiler bundle здесь:

```text
tools/AtlusScriptTools/
  AtlusScriptCompiler.exe
  Libraries/
  Charsets/
  runtimes/
  ...
```

Если bundle лежит на месте, `project.Build()` и `project.build()` могут собирать
`.bf` вообще без аргумента `compiler_path`.

## Минимальный пример

```python
from p4gscript import P4GProject, bitChk

project = P4GProject("mod_hello", encoding="P4G_EFIGS", safety="beginner")

done = project.reserve_bit(
    "MOD_HELLO_DONE",
    reason="prevents repeated test message",
)

message = project.message("MOD_HELLO")
message.line("Hello from Python-generated MessageScript.")

proc = project.procedure("MOD_HELLO_TEST")
with proc.if_(bitChk(done) == 0):
    proc.help_msg(message)
    proc.bit_on(done)

project.write("build")
```

Результат:

```text
build/mod_hello.flow
build/mod_hello.msg
```

## Компиляция в `.bf`

```python
project.compile("build")
```

Или совсем коротко:

```python
result = project.Build()
```

По умолчанию это создаст папку:

```text
./build/<project_name>/
```

и положит туда `.flow`, `.msg`, `.bf`, `manifest.json`, `manifest.txt`.

Для английской P4G библиотека использует:

```text
-Library P4G
-Encoding P4G_EFIGS
-OutFormat V1
```

Для японских файлов:

```python
project = P4GProject("mod_name", encoding="P4G_JP")
```

## Новый скрипт или patch существующего

Пользовательский уровень не должен требовать поиска системных путей. Компилятор уже bundled в
`tools/AtlusScriptTools/`, а для самых частых P4G-сценариев библиотека теперь умеет короткие
constructor-helper'ы.

Создать новый field script без ручного `Empty(...)` и без ручного target path:

```python
from p4gscript import P4GProject, Speaker

project = P4GProject.new_field_script(
    "f007_nanako_greeting",
    "f007_nanako_greeting",
    safety="beginner",
)

proc = project.procedure("MOD_NANAKO_GREETING")
with proc.during(4, 1, 5, 6):
    proc.say(Speaker.NANAKO, "Good morning!")

project.Build()
```

Patch существующего field script, если пользователь положил `f007.bf` рядом со своим `.py`:

```python
from pathlib import Path
from p4gscript import P4GProject, Speaker

project = P4GProject.patch_field_script(
    "f007_nanako_greeting",
    "f007",
    Path(__file__).with_name("f007.bf"),
    import_path="original_f007.bf",
    safety="beginner",
)

hook = project.replace_hook("select_nanako_okaeri")
with hook.during(4, 1, 5, 6):
    hook.say(Speaker.NANAKO, "Good morning!")
hook.call_original()

project.Build(Debug=True)
```

Если нужен старый низкоуровневый стиль, он никуда не делся:

- `Empty(...)` — создать новый script без оригинального `.bf`;
- `BF(...)` — импортировать существующий `.bf` и собрать patch/hook;
- `FieldEmpty(...)` / `FieldBF(...)` — те же сценарии, но уже с автоматическим field target path;
- `field_target("f007")` и `event_target("E860_074A")` — готовые target-path helper'ы.

## Короткие helper'ы для мод-кода

Для самых частых проверок и действий больше не обязательно писать длинные выражения вручную:

```python
from p4gscript import P4GProject, Speaker, TimeOfDay, timeOfDay

project = P4GProject.new_field_script("easy_mod", "easy_mod", safety="beginner")
done = project.reserve_bit("MOD_EASY_DONE")
proc = project.procedure("MOD_EASY_PROC")

with proc.once(done, condition=timeOfDay() == TimeOfDay.EVENING):
    proc.say(Speaker.NANAKO, "Hello once!")
```

Самые полезные новые сокращения:

- `proc.during(4, 1, 5, 6)` вместо `proc.if_(checkTimeSpan(...) == 1)`;
- `proc.when_time(TimeOfDay.EVENING)` для проверки времени суток;
- `proc.when_bit_clear(done)` и `proc.when_bit_set(done)` для частых bit-check'ов;
- `proc.once(done, condition=...)` для одноразовых действий с автоматическим `BIT_ON(done)`;
- `choice = proc.ask("choice", "Go out", "Stay home")` для коротких selection-блоков;
- `proc.add_yen(...)`, `proc.set_item(...)`, `proc.get_item(...)`, `proc.set_msg_var(...)` для частых игровых действий.
## Что умеет библиотека

- генерировать `.flow`;
- генерировать `.msg`;
- создавать `procedures`;
- работать с `bits`, `counts`, `messages`, `selections`;
- строить hook-процедуры;
- резервировать свободные mod-bit'ы;
- запускать `AtlusScriptCompiler`;
- анализировать декомпилированный `script_workspace`;
- строить conflict report;
- работать в safety-режимах для новичка и expert-style workflow.

## Самые полезные файлы

### Примеры

- `examples/mod_project.py` - минимальный buildable проект;
- `examples/patch_project.py` - пример patch/hook по оригинальному `.bf`, который пользователь кладёт рядом с `.py`;
- `examples/nanako_evening_follow_along.py` - учебный проект для первого hook-мода с Nanako.

`.bf` файлы специально игнорируются git. Они нужны локально для сборки patch-модов,
но не должны попадать в репозиторий вместе с библиотекой.

### Документация

- `docs/index.html` - пошаговое обучение по библиотеке `p4gscript`;
- `docs/reference.html` - справочник функций, объектов и helper'ов;
- `ROADMAP.md` - что делать дальше с библиотекой.

## CLI

Если пакет установлен, доступна команда:

```powershell
p4gscript --help
```

Без установки:

```powershell
$env:PYTHONPATH="src"
py -m p4gscript --help
```

Примеры:

```powershell
$env:PYTHONPATH="src"
py -m p4gscript summary --workspace ..\Samples\P4G_Steam_Test\script_workspace
```

```powershell
$env:PYTHONPATH="src"
py -m p4gscript build .\examples\mod_project.py --out .\build
```

## Прямой запуск Python-проекта

У buildable-примеров есть блок:

```python
if __name__ == "__main__":
    build_project().Build()
```

Поэтому их можно запускать вообще без CLI-аргументов:

```powershell
$env:PYTHONPATH="src"
py .\examples\mod_project.py
```

## Analyzer

```python
from p4gscript import WorkspaceAnalyzer

workspace = WorkspaceAnalyzer.load("../Samples/P4G_Steam_Test/script_workspace")

print(workspace.summary())
print(workspace.native_call("BIT_CHK"))
print(workspace.procedures_named("SCR_ONLY_NPC_YOUSUKE"))
print(workspace.bit_usages(2531))
```

Analyzer полезен для двух вещей:

1. понять, как устроены оригинальные скрипты;
2. заранее увидеть конфликты с уже используемыми `bits`, именами процедур и message IDs.

## Тесты

Запуск:

```powershell
py -m pytest tests
```

Часть тестов использует локальный `Samples/P4G_Steam_Test/script_workspace`, поэтому
если workspace рядом с репозиторием отсутствует, эти тесты будут автоматически
пропускать тяжелые сценарии.

## Важная граница проекта

`p4gscript` не исполняется игрой напрямую.

Pipeline всегда такой:

```text
Python
  -> generated .flow
  -> generated .msg
  -> AtlusScriptCompiler
  -> .bf
  -> mod package / override
  -> game
```

То есть библиотека делает Persona scripting понятнее, но не отменяет знание того,
как устроены `.flow`, `.msg`, `bits`, `scheduler`, `field` и `event scripts`.



