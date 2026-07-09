# Persona 4 Golden Mod Survey

## Область исследования

Я просканировал моды из `E:\Reloaded-II\Mods`, чьи папки начинаются с:

- `p4g`
- `p4g64`
- `p4gpc`
- `p4r`

Цель была такой:

1. найти все `.bf`, `.flow`, `.msg`, `.msg.h`;
2. отделить реальные compiled-скрипты от пустых заглушек;
3. декомпилировать все непустые `.bf` в `.flow/.msg/.msg.h`;
4. понять, какие техники реально используют другие авторы модов;
5. извлечь выводы, полезные для `pyFlowCompile`.

Артефакты исследования:

- `analysis/mod_survey/output/inventory.json`
- `analysis/mod_survey/output/...` — декомпилированные результаты
- `analysis/mod_survey/run_reloaded_mod_survey.ps1`
- `analysis/mod_survey/surprise_mod/...` — тестовая модификация

## Сводка по числам

По результатам сканирования:

- всего модов по заданным префиксам: `39`
- модов, где есть скриптовые следы (`.bf`, `.flow`, `.msg`): `18`
- модов с реальными непустыми `.bf`: `6`
- модов, где `.bf` есть, но это только пустые заглушки: `11`
- модов без скриптовых файлов: `21`
- всего найдено `.bf`: `67`
- из них реальных непустых `.bf`: `16`
- пустых `.bf`: `51`
- исходников `.flow`: `86`
- исходников сообщений `.msg` / `.msg.h`: `75`

## Ключевое наблюдение про `.bf`

Самое важное открытие: в сообществе P4G очень часто `.bf` в структуре мода не является настоящим редактируемым исходником.

Типичный паттерн такой:

1. в runtime-пути лежит пустой `0-byte` `.bf`, чтобы соблюсти layout override;
2. реальный редактируемый код лежит рядом в `FEmulator\\BF\\...` как `.flow` и `.msg`;
3. реальный build производится из этих `.flow/.msg`, а не из пустышки.

Это не догадка на пустом месте, а вывод из нескольких фактов:

- попытка декомпилировать такие файлы сразу ломается, потому что размер `0`;
- рядом почти всегда лежат рабочие `.flow` / `.msg`;
- в модах с реально собранным результатом лежат уже непустые `.bf`, которые нормально декомпилируются.

Характерные примеры:

- `p4g64.text.welcomehome` — пустой `f007.bf`, но есть `FEmulator\\BF\\f007.msg`;
- `p4g64.dungeonSavePoints` — много placeholder `.bf`, но логика лежит в `.flow`;
- `p4gscript.test_mode_dialog` — уже есть реальный compiled `.bf`, и он декомпилируется без проблем.

## Чем я декомпилировал `.bf`

Для реальных `.bf` использовалась команда вида:

```powershell
tools\AtlusScriptTools\AtlusScriptCompiler.exe `
  -Decompile `
  -In <input.bf> `
  -Out <output.flow> `
  -Library P4G `
  -Encoding P4G_EFIGS
```

Что выяснилось по кодировкам:

- для `data_e.cpk` и большинства PC field override нужен `P4G_EFIGS`;
- для части контента в `data.cpk` логично использовать `P4G_JP`;
- `AtlusScriptCompiler` здесь полезнее, чем отдельные extractor-утилиты.

## Как сообщество реально пакует скриптовые моды

На практике встретились три модели:

### 1. Placeholder `.bf` + исходники `.flow/.msg`

Это самый частый сценарий для field/script mods под Reloaded II.

Обычно структура такая:

```text
FEmulator\BF\<script>.flow
FEmulator\BF\<script>.msg
FEmulator\PAK\field\pack\<arc>\<script>.bf   <- пустой placeholder
```

Плюсы:

- человеку удобно читать и править исходник;
- hook-логика явно видна;
- мод проще сопровождать.

### 2. Только compiled `.bf`

Таких модов меньше. Это либо финальный собранный артефакт, либо мод, где автор не положил исходники.

Примеры:

- `p4g.v.junespoints`
- `p4r.v.aikarestore`

### 3. Смешанный вариант

Самый интересный и самый практичный сценарий:

- часть скриптов положена как готовые `.bf`;
- часть как `.flow/.msg`;
- иногда рядом есть локализация;
- иногда ещё есть DLL, которая расширяет поведение.

Лучший пример — `p4g64.customSubMenu`.

## Что вообще можно сделать через P4G-скрипты

После чтения чужих модов видно, что возможности у field/event/battle script довольно широкие.

### 1. Менять диалоги и подсказки

Самый простой уровень:

- заменять реплики;
- менять help text;
- править prompt selection;
- исправлять уведомления.

Примеры:

- `p4g64.text.welcomehome`
- `p4g64.betterFishing`
- `p4g.script.dungeon_text_fixes.rudiger__gb`

### 2. Перехватывать домашние и полевые interaction points

Можно врезаться в существующие процедуры поля и менять поведение:

- выход из дома;
- проверка дивана;
- кухня;
- вход в дверь;
- быстрые переходы;
- town map.

Характерные хуки:

- `call_lmap_hook`
- `door_entrance_hook`
- `check_sofa_p4p_hook`
- `check_kitchen_hook`

### 3. Менять расписание и дневные маршруты

Можно влиять на:

- scheduler-переходы;
- точки входа в события;
- availability событий по датам;
- ночные действия персонажей.

Характерные хуки:

- `sdl01_28_AM_A_hook`
- `sdl01_28_AM_B_hook`
- `sdl01_29_AM_A_hook`
- `sdl04_10_PM_D_hook`

### 4. Делать новые меню и новые ветки выбора

Это уже серьёзный уровень:

- собственные selection menus;
- custom travel order;
- dungeon options;
- дополнительные команды в существующих местах.

Здесь особенно выделяется `p4g64.customSubMenu`.

### 5. Управлять битами, счётчиками, предметами и социальными статами

Это фундамент почти всех модов.

Чаще всего используются:

- `BIT_CHK`
- `BIT_ON`
- `BIT_OFF`
- `GET_CNT`
- `SET_CNT`
- `GET_ITEM`
- `SET_ITEM`
- `ADD_YEN`
- `SET_MSG_VAR`
- `GET_SOCIAL_STATS`
- `GET_SL_LEVEL`

Именно вокруг этого нужно строить удобные beginner-helper'ы в библиотеке.

### 6. Возвращать вырезанные события и встраивать новые

Это реальный и уже используемый сценарий.

Примеры:

- `p4g.restoredwinterevents.espneng`
- `p4r.v.aikarestore`

Техники:

- `CALL_EVENT`
- проверки дат;
- проверки условий сюжета;
- подмена scheduler flow.

### 7. Менять dungeon-логику

Можно делать:

- save points;
- floor options;
- escape behavior;
- dungeon menu injections;
- chest / Reaper related behavior.

Характерные хуки:

- `save_point_hook`
- `dng_tbox_hook`
- `death_check_hook`
- `common_floor_change_hook`
- `dng_escape_hook`

### 8. Менять battle AI

Это тоже не теоретическая возможность, а реальный мод.

Пример:

- `p4gpc.culpritbossaifix64`

Используются battle/AI функции вроде:

- `AI_USE_SKILL`
- `AI_TAR_RND`
- `AI_TAR_SELF`
- `AI_MY_HOJO`
- `AI_EN_HAS_AILMENT`

### 9. Локализовывать моды

В нескольких модах видно, что авторы отдельно кладут локализованные message/script assets.

Это значит, что библиотеке в перспективе нужны:

- удобная работа с `.msg`;
- поддержка нескольких наборов сообщений;
- возможно, потом генерация L10N-структур.

### 10. Комбинировать `.bf` с DLL

Некоторые моды совмещают скрипты и код на стороне плагина.

Это полезно понимать: не всё в P4G нужно решать самим FlowScript'ом.

Примеры:

- `p4g64.customSubMenu`
- `p4g.qol.nongplussuperboss`

## Разбор скриптовых модов

Ниже перечислены моды, где были найдены скриптовые артефакты.

### `p4g.qol.nongplussuperboss`

- Тип: placeholder `.bf` + `.flow`
- Основная идея: убрать требование `NG+` для секретного босса и сделать доступ понятнее
- Важные файлы:
  - `FEmulator\BF\f008.flow`
  - `FEmulator\BF\f020.flow`
- Хуки:
  - `sdl03_20_AM_A_hook`
  - `velvet_room_hook`
- Техники:
  - проверки битов и предметов;
  - изменение условий доступа;
  - переход в нужное событие или dungeon flow.

### `p4g.restoredwinterevents.espneng`

- Тип: mixed
- Есть реальные `.bf`, которые успешно декомпилировались
- Назначение: вернуть вырезанные зимние события
- Важные файлы:
  - `FEmulator\BF\scheduler_01.flow`
  - декомпилированные `E449_001A.flow/.msg`
- Хуки:
  - `sdl01_28_AM_A_hook`
  - `sdl01_28_AM_B_hook`
  - `sdl01_29_AM_A_hook`
- Техники:
  - `CALL_EVENT`;
  - scheduler routing;
  - завязка на календарные даты.

### `p4g.script.dungeon_text_fixes.rudiger__gb`

- Тип: message-only + placeholder `.bf`
- Назначение: правка dungeon text и prompt behavior
- Важный файл:
  - `FEmulator\BF\dungeon.msg`
- Вывод:
  - далеко не все полезные моды требуют сложную flow-логику;
  - одной корректной message-правки уже достаточно для заметного QoL.

### `p4g.v.junespoints`

- Тип: compiled-only
- Реальный `.bf` декомпилирован успешно
- Важный декомпилированный результат:
  - `analysis/mod_survey/output/p4g.v.junespoints/P5REssentials/CPK/data_e/event_data/script/E860_074A.flow`
- Что делает:
  - меняет награды и очки за поездки в Junes;
  - работает на уровне event-script.
- Замеченные техники:
  - `RNG`
  - `SET_ITEM`
  - `SET_MSG_VAR`
  - ветвления по датам.

### `p4g64.betterFishing`

- Тип: message/data-text mod
- Основной интерес:
  - показывает, что мод может быть полезным вообще без field hook;
  - иногда достаточно исправить help/item text.
- Важный файл:
  - `FEmulator\BMD\init.bin\init\datMsg.pak\datItemHelp.msg`

### `p4g64.betterQuizzes`

- Тип: placeholder `.bf` + `.flow`
- Идея: сделать школьные вопросы дружелюбнее
- Важные файлы:
  - `FEmulator\BF\n006_001.flow`
  - `FEmulator\BF\n006_003.flow`
- Хуки:
  - `scr_npc_kashiwagi_q_59_hook`
  - `scr_npc_kashiwagi_q_74_hook`
  - `NPC_07_hook`
- Техники:
  - изменение `SEL`;
  - повтор вопроса;
  - выдача предметов;
  - completion bits и счётчики.

### `p4g64.craneGameRebalanced`

- Тип: placeholder `.bf` + `.flow`
- Важный файл:
  - `FEmulator\BF\f011.flow`
- Хук:
  - `ufo_catcher_hook`
- Техники:
  - правка RNG;
  - изменение правил доступности;
  - правка наград и попыток.

### `p4g64.customSubMenu`

- Тип: большой mixed mod
- Это самый важный референс во всей выборке
- Есть:
  - много `.flow`;
  - много `.msg`;
  - реальные compiled `.bf`;
  - DLL;
  - локализация.
- Характерные файлы:
  - `FEmulator\BF\f007.flow`
  - `FEmulator\BF\field.flow`
  - `FEmulator\BF\lmap.flow`
  - `FEmulator\BF\scheduler_04.flow`
  - `FEmulator\BF\OtherMods\...`
  - `FEmulator\BF\ModMenu\ModMenu.flow`
- Что демонстрирует:
  - построение полноценного кастомного меню;
  - объединение нескольких подпроектов через imports;
  - работу с travel order;
  - social link анализ;
  - dungeon/menu расширения;
  - совместимость с другими модами.
- Репрезентативные хуки:
  - `call_lmap_hook`
  - `door_entrance_hook`
  - `field_order_hook`
  - `school_order_hook`
  - `night_place_order_exit_hook`
  - `fox_recover_hook`
  - `sel_000_hook`
  - `sdl04_10_PM_D_hook`
  - `dng_tbox_hook`
  - `dng_decease_hook`

### `p4g64.dungeonSavePoints`

- Тип: placeholder `.bf` + `.flow`
- Идея: добавить points сохранения в данжи
- Важные файлы:
  - `FEmulator\BF\f023.flow`
  - `FEmulator\BF\f024.flow`
  - `FEmulator\BF\f025.flow`
  - `FEmulator\BF\f026.flow`
  - `FEmulator\BF\f027.flow`
  - `FEmulator\BF\f028.flow`
  - `FEmulator\BF\f029.flow`
  - `FEmulator\BF\f030.flow`
  - `BF\saveOnly.flow`
- Хуки:
  - `f023_002_init_hook`
  - `f024_002_init_hook`
  - `f025_002_init_hook`
  - `f026_002_init_hook`
  - `f027_002_init_hook`
  - `f028_002_init_hook`
  - `f029_002_init_hook`
  - `f030_001_init_hook`
  - `save_point_hook`
- Техники:
  - загрузка field object;
  - принудительный save interaction;
  - проверки битов и времени;
  - точечное вмешательство в init-скрипты карты.

### `p4g64.eveningHangoutImprovements`

- Тип: placeholder `.bf` + большой набор `.flow`
- Очень сильный референс для social link / night logic
- Что делает:
  - расширяет вечерние hangout-сценарии;
  - меняет availability и вывод сообщений.
- Характерные хуки:
  - `SCR_NIGHT_NPC_YOUSUKE_hook`
  - `SCR_NIGHT_NPC_KANJI_hook`
  - `SCR_NIGHT_NPC_CHIE_hook`
  - `SCR_NIGHT_NPC_YUKIKO_hook`
  - `SCR_NIGHT_NPC_RISE_hook`
  - `SCR_NIGHT_NPC_NAOTO_hook`
  - `SCR_NIGHT_NPC_EBI_hook`
  - `EVE_MES_*_hook`
  - `EVE_END_SYSMES_*_hook`
  - `COMMUNITY_POINT_*_hook`
- Техники:
  - проверки social link условий;
  - ветвления по датам и флагам;
  - отдельные dialog/result flows на каждого персонажа.

### `p4g64.hyperspeedReading+`

- Тип: placeholder `.bf` + `.flow`
- Важный файл:
  - `FEmulator\BF\f007.flow`
- Хук:
  - `check_sofa_p4p_hook`
- Что показывает:
  - одна точка дома может стать большой новой механикой;
  - house-interaction mods очень практичны и удобны для тестов.

### `p4g64.produceStore`

- Тип: mixed
- Есть реальный `.bf` и несколько `.flow`-вариантов
- Важные файлы:
  - `BF\Winter Vegetables\n007_001_hooks.flow`
  - `BF\Winter Vegetables\n009_004_hooks.flow`
  - `BF\No Winter Vegetables\...`
- Хук:
  - `NPC_PLANT_SELLER_hook`
- Техники:
  - управление ассортиментом магазина по датам;
  - проверки social link;
  - выдача и продажа предметов;
  - варианты поведения по конфигурации.

### `p4g64.text.welcomehome`

- Тип: message-only + placeholder `.bf`
- Что делает:
  - меняет домашние реплики Nanako / Dojima в `f007`
- Важный файл:
  - `FEmulator\BF\f007.msg`
- Практический смысл:
  - это один из самых чистых примеров modding-а только через `.msg`.

### `p4g64.unmissableBooks`

- Тип: placeholder `.bf` + `.flow`
- Важные файлы:
  - `FEmulator\BF\book.flow`
  - `FEmulator\BF\f011.flow`
- Хуки:
  - `book_greet_hook`
  - `city_bookstore_hook`
- Техники:
  - контроль доступности книг;
  - одноразовые объявления;
  - управление stock progression.

### `p4gpc.culpritbossaifix64`

- Тип: placeholder `.bf` + `.flow`
- Важный файл:
  - `FEmulator\BF\enemy.flow`
- Хук:
  - `enemyAI_d_adachi_hook`
- Что особенно важно:
  - это прямое доказательство, что библиотека может быть полезна не только для field, но и для battle/script logic.

### `p4gpc.dojimasCoffee`

- Тип: placeholder `.bf` + `.flow`
- Важный файл:
  - `FEmulator\BF\f007.flow`
- Хуки:
  - `f007_002_init_hook`
  - `check_kitchen_hook`
- Техники:
  - новая домашняя interaction;
  - проверки состояния усталости;
  - эффекты, fade, object state.

### `p4gscript.test_mode_dialog`

- Тип: рабочий smoke-test для твоего подхода
- Есть реальные compiled `.bf`
- Важные файлы:
  - `Source\f007_test_mode_dialog.flow`
  - `Source\f007_test_mode_dialog.msg`
- Хук:
  - `call_lmap_hook`
- Почему этот мод важен:
  - он подтверждает рабочий паттерн:
    - импорт оригинального `f007.bf`;
    - создание hook-процедуры;
    - вызов `call_lmap_unhooked()` после своей логики;
    - сборка в override path.

### `p4r.v.aikarestore`

- Тип: compiled-only
- Добавлен в исследование, потому что попал под заданный префикс `p4r`
- Реальный `.bf` декомпилирован успешно
- Что показывает:
  - event restoration работает на тех же базовых инструментах: стат-проверки, предметы, деньги, сообщения.

## Наблюдения по точкам входа

Повторяющиеся типы hook point'ов:

- домашние и полевые действия:
  - `call_lmap_hook`
  - `door_entrance_hook`
  - `check_kitchen_hook`
  - `check_sofa_p4p_hook`
- NPC и social link логика:
  - `SCR_NIGHT_NPC_*_hook`
  - `NPC_PLANT_SELLER_hook`
  - `book_greet_hook`
- scheduler / story routing:
  - `sdl*_hook`
- dungeon:
  - `*_init_hook`
  - `save_point_hook`
  - `dng_*_hook`
- battle:
  - `enemyAI_*_hook`

Практический вывод: моды редко создают поведение "с нуля". Почти всегда они встраиваются в уже существующую точку исполнения через hook.

## Моды без script-файлов

Ниже перечислены моды, где в рамках этого исследования не было найдено `.bf/.flow/.msg`, но они всё равно полезны как обзор того, чем живёт экосистема.

- `p4g.model.igor_blinks.rudiger__gb` — правка модели Igor
- `p4g64.calendarPack` — замена календаря в комнате героя
- `p4g64.colourfulPartyPanel` — цветной party panel
- `p4g64.fogrestoration` — восстановление визуалов Persona 4 PS2
- `p4g64.thirdsemskill` — баланс third semester skills
- `p4g64.v.foyfix` — bugfix скилла финального босса
- `p4gpc.animatedcutins` — анимированные cut-in
- `p4gpc.assets.aoafix` — фиксы all-out attack cut-ins
- `p4gpc.colorfulcutins64` — цветные critical cut-ins
- `p4gpc.colorfulskills_p4g` — цветные иконки skills/items
- `p4gpc.controlleruioverhaul_colorful` — overhaul controller prompts
- `p4gpc.gentlefastforward_brown` — замена fast-forward SFX и visual effects
- `p4gpc.inaba` — startup patcher / exe patching
- `p4gpc.inputlibrary` — библиотека для чтения и записи input
- `p4gpc.musicenhancementpack` — музыкальные улучшения
- `p4gpc.notvstatic64` — удаление TV static / glare
- `p4gpc.restoredgameovermusic` — возврат оригинальной музыки game over
- `p4gpc.texturefixespack64` — большой пакет texture/UI fixes
- `p4gpc.tinyadditions` — мелкие улучшения игры
- `p4gpc.titlescreenfix` — fixes title sequence + надпись про mod loader
- `p4gpc.universecard` — визуальная правка World Card

Вывод по этой группе простой: экосистема P4G живёт не только на скриптах. Для полноценного инструментария полезно думать и о соседних форматах, но для `pyFlowCompile 1.0` это уже вторично.

## Что это означает для твоей библиотеки

Из всего исследования следуют довольно жёсткие выводы по приоритетам.

### 1. Основной сценарий должен быть hook-first

Библиотека должна в первую очередь упрощать не "написание абстрактного `.flow`", а внедрение кода в существующий script entrypoint.

То есть удобным должен быть сценарий:

1. указать оригинальный `.bf`;
2. импортировать его;
3. объявить hook-процедуру;
4. при необходимости вызвать `*_unhooked()`;
5. собрать результат сразу в правильный override path.

### 2. `Empty()` нужен, но это не главный путь

Полностью новый script с нуля возможен, но по реальной практике модов это не основной workflow.

Главный workflow:

- взять существующий скрипт;
- встроиться в понятную точку;
- оставить оригинальное поведение живым;
- добавить свою логику рядом.

### 3. `create_script: bool` — разумная опция

Это хорошо соответствует двум реальным сценариям:

- `create_script = true` — создаём новый script asset;
- `create_script = false` — работаем как hook/patch над существующим файлом.

### 4. Beginner-режим действительно нужен

После просмотра чужих модов видно, что самые частые операции повторяются постоянно:

- проверки битов;
- проверки времени и дат;
- работа со счётчиками;
- вывод сообщений;
- выбор через `SEL`;
- выдача наград;
- переходы по полям и событиям.

Значит, `safety="beginner"` должен закрывать именно это ядро.

### 5. Standard-режим тоже нужен

Есть моды, которые используют более редкие или более "грязные" вещи:

- battle AI;
- dungeon helper logic;
- scheduler overrides;
- field object functions;
- более низкоуровневые операции.

Их нельзя прятать навсегда. Их надо просто вынести в более широкий режим API.

### 6. Библиотеке нужна предметная группировка helper'ов

Не просто свалка функций, а набор модулей по доменам:

- `bits`
- `time/date`
- `message/dialog`
- `selection`
- `inventory/shop`
- `social_link`
- `field/travel`
- `dungeon`
- `battle_ai`
- `scheduler`

### 7. Особо важен `f007`

По чужим модам видно, что `f007` — одна из лучших тестовых площадок:

- дом героя;
- ночные переходы;
- диван;
- кухня;
- домашние диалоги.

Для обучения и smoke tests это почти идеальная карта.

## Тестовая модификация, которая может удивить

Я уже собрал отдельную тестовую модификацию:

- `analysis/mod_survey/surprise_mod/README.md`
- `analysis/mod_survey/surprise_mod/Source/f007_night_bonus.flow`
- `analysis/mod_survey/surprise_mod/Source/f007_night_bonus.msg`
- `analysis/mod_survey/surprise_mod/build/f007.bf`

Что делает мод:

- хукает `call_lmap` в `f007`;
- срабатывает только ночью;
- перед обычным выходом из дома показывает скрытый бонус-выбор;
- даёт игроку один из вариантов:
  - `3000 yen`
  - `Courage +`
  - `Knowledge +`
  - `Ignore`
- затем возвращает управление оригинальному `call_lmap`.

Почему я выбрал именно такой сценарий:

- он опирается на реально встречающийся community-паттерн;
- легко проверяется в игре;
- он заметнее обычной замены текста;
- он одновременно проверяет hook, message, selection и reward logic.

## Статус surprise mod

Что уже проверено:

- мод успешно собран в `.bf`;
- обратная декомпиляция собранного `.bf` тоже успешна;
- артефакты разложены в override-структуру.

Что ещё не проверено:

- живое поведение внутри игры.

То есть по toolchain всё выглядит корректно, но окончательная проверка — только in-game.

## Что стоит делать дальше

Следующий практический шаг уже не исследовательский, а интеграционный:

1. поставить `surprise_mod` в Reloaded II;
2. проверить, срабатывает ли hook на ночном выходе из `f007`;
3. если hook не вызывается, смотреть:
   - правильность target path;
   - правильность точки хука;
   - порядок загрузки модов;
   - не перекрывает ли тот же `f007.bf` другой мод.

## Короткий итог

По этому обзору видно следующее:

- у P4G-моддинга очень сильная hook-культура;
- реальные моды чаще патчат существующие сценарии, чем строят всё с нуля;
- `.flow/.msg` важнее для автора мода, чем placeholder `.bf`;
- `f007`, scheduler, social links, dungeon init и battle AI — это реальные рабочие зоны для библиотеки;
- твоя идея с `beginner/standard` соответствует тому, как на самом деле распределяется сложность в чужих модах.
