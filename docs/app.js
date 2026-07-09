const referenceItems = [
  {
    id: "p4gproject",
    name: "P4GProject",
    category: "core",
    section: "project",
    level: "both",
    signature: 'P4GProject(name, encoding="P4G_EFIGS", safety="standard", source=None, create_script=True, ...)',
    summary: "Главный объект сборки. В нём живёт весь будущий мод: source, hooks, процедуры, messages, selections, bits и вызов Build().",
    why: "Создавай один P4GProject на один собираемый script container. Через него ты описываешь всё содержимое будущего .flow/.msg/.bf.",
    notes: [
      "Если source указывает на BF(...), проект работает как patch существующего скрипта.",
      "Если source указывает на Empty(...), проект создаёт новый container и сам по себе не гарантирует игровой вызов.",
      "Через этот объект создаются messages, selections, процедуры и hooks.",
    ],
    example: `project = P4GProject(
    "hello_scheduler",
    source=SCRIPT,
    safety="beginner",
)`,
    result: "Возвращает объект проекта, на котором дальше вызываются message(), procedure(), replace_hook() и Build().",
  },
  {
    id: "bf",
    name: "BF",
    category: "core",
    section: "project",
    level: "both",
    signature: "BF(path, *, import_path=None, target=None, copy=True)",
    summary: "Описывает существующий .bf файл как основу для patch-build.",
    why: "Используй BF(), когда хочешь вмешаться в уже существующий игровой скрипт и добавить hook к его процедурам.",
    notes: [
      "path указывает на оригинальный .bf на диске.",
      "import_path — имя, под которым этот файл будет импортирован в generated flow-проект.",
      "target — ожидаемый игровой путь для итогового файла внутри мода.",
    ],
    example: `SCRIPT = BF(
    Path(__file__).with_name("f007.bf"),
    import_path="original_f007.bf",
    target="data_e.cpk/field/script/f007.bf",
)`,
    result: "Возвращает ScriptSource для передачи в P4GProject(source=...).",
  },
  {
    id: "empty",
    name: "Empty",
    category: "core",
    section: "project",
    level: "both",
    signature: "Empty(*, target=None)",
    summary: "Создаёт source без исходного .bf файла. Используется для сборки нового script container.",
    why: "Нужен, когда ты не патчишь существующий скрипт, а создаёшь свой собственный container.",
    notes: [
      "Новый .bf не будет вызван автоматически. Игре всё равно нужен путь, по которому она обратится к нему.",
      "Подходит для advanced-сценариев, когда у тебя уже есть понятный механизм вызова нового скрипта.",
    ],
    example: `project = P4GProject(
    "mod_dialogue",
    source=Empty(target="data_e.cpk/field/script/mod_dialogue.bf"),
)`,
    result: "Возвращает ScriptSource для standalone-сборки.",
  },
  {
    id: "build",
    name: "Build",
    category: "core",
    section: "project",
    level: "both",
    signature: "project.Build(out_dir=None, *, compile_bf=True, Debug=False, ...)",
    summary: "Запускает полную сборку проекта: рендер .flow/.msg, компиляция и выпуск итогового .bf.",
    why: "Это финальный шаг после описания логики. Именно Build() превращает Python-описание мода в реальные артефакты.",
    notes: [
      "Debug=True включает более подробные логи компилятора.",
      "В результате доступны пути к flow, msg и bf файлам.",
    ],
    example: `result = build_project().Build(Debug=True)
print(result.flow_path)
print(result.msg_path)
print(result.bf_path)`,
    result: "Возвращает BuildResult с путями к сгенерированным файлам.",
  },
  {
    id: "reserve-bit",
    name: "project.reserve_bit",
    category: "core",
    section: "project",
    level: "both",
    signature: 'project.reserve_bit(name, *, reason=None, safe=True)',
    summary: "Резервирует mod bit и регистрирует его в проекте как понятный именованный идентификатор.",
    why: "Используй это почти всегда, когда мод должен помнить своё состояние: показывал ли сообщение, был ли уже выполнен кусок сценария, доступен ли следующий шаг.",
    notes: [
      "Результат удобно передавать в bitChk(), bit_on() и bit_off().",
      "Именованный bit делает generated flow заметно понятнее, чем голые числа.",
    ],
    example: `shown = project.reserve_bit(
    "MOD_HELLO_WORLD_SHOWN",
    reason="show greeting once",
)`,
    result: "Возвращает BitId, совместимый с helpers и методами Procedure.",
  },
  {
    id: "message-method",
    name: "project.message",
    category: "messages",
    section: "messages",
    level: "both",
    signature: "project.message(name, *, speaker=None, portrait=None)",
    summary: "Создаёт MessageScript-блок [msg ...], который потом можно показать через MSG(...).",
    why: "Когда текст должен существовать как отдельный message resource, а не как одноразовая строка внутри say(...).",
    notes: [
      "В message.line(...) добавляются отдельные строки с тегами и настройками.",
      "name — это символическое имя, которое потом увидит generated flow.",
      "Если speaker — Character.YOSUKE, message получает и имя, и стандартный bustup-портрет.",
      "portrait можно передать отдельно, если имя и портрет должны браться из разных источников.",
    ],
    example: `msg = project.message("MOD_INTRO", speaker=Character.YOSUKE)
msg.line("Сегодня ты тестируешь диалоговую систему.")`,
    result: "Возвращает Message для дальнейшего наполнения строками.",
  },
  {
    id: "selection-method",
    name: "project.selection",
    category: "messages",
    section: "messages",
    level: "both",
    signature: 'project.selection(name, *, pattern="top")',
    summary: "Создаёт selection block [sel ...] для вариантов ответа или действия.",
    why: "Используй, когда игрок должен выбрать опцию, а ты потом хочешь проверить индекс выбора.",
    notes: [
      "Пункты добавляются через selection.option(...).",
      "Показ выполняется через proc.sel(variable, selection).",
    ],
    example: `choices = project.selection("MOD_CHOICES")
choices.option("Да, продолжаем")
choices.option("Нет, вернёмся позже")`,
    result: "Возвращает Selection.",
  },
  {
    id: "procedure-method",
    name: "project.procedure",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: 'project.procedure(name, *, return_type="void", params="")',
    summary: "Создаёт обычную FlowScript-процедуру внутри проекта.",
    why: "Нужна для логики, которую ты сам хочешь определить как отдельную функцию внутри generated flow.",
    notes: [
      "Созданная процедура не обязана быть вызвана игрой автоматически.",
      "Часто используется как helper-процедура, которую потом вызывает hook или другой код.",
    ],
    example: `proc = project.procedure("main")
proc.say(Speaker.NANAKO, "Привет.")`,
    result: "Возвращает Procedure builder.",
  },
  {
    id: "replace-hook",
    name: "project.replace_hook",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: 'project.replace_hook(target, *, return_type="void", params="")',
    summary: "Создаёт replace-hook для процедуры target и рендерит имя target_hook().",
    why: "Это главный способ встроиться в уже существующую игровую точку входа и полностью заменить поведение процедуры.",
    notes: [
      "Если нужен оригинал, вызывай proc.call_original() вручную.",
      "Для первого smoke-test hooks обычно лучше любого standalone script.",
    ],
    example: `hook = project.replace_hook("everymorning")
hook.call_original()`,
    result: "Возвращает Procedure, привязанный к hook-имени target_hook.",
  },
  {
    id: "soft-hook",
    name: "project.soft_hook",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: 'project.soft_hook(target, *, return_type="void", params="")',
    summary: "Создаёт soft hook и рендерит target_softhook().",
    why: "Используй, когда тебе нужен hook-подход с семантикой soft/before, а не жёсткая replace-подмена.",
    notes: [
      "Подходит для сценариев, где ты хочешь аккуратно встроиться до основного поведения.",
      "Фактическая полезность зависит от того, как конкретный target используется в игре.",
    ],
    example: `hook = project.soft_hook("some_proc")
hook.say(Speaker.NANAKO, "Я сработала до оригинала.")`,
    result: "Возвращает Procedure для target_softhook.",
  },
  {
    id: "after-hook",
    name: "project.after_hook",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: 'project.after_hook(target, *, return_type="void", params="")',
    summary: "Создаёт after hook и рендерит target_hookafter().",
    why: "Используй, когда логика должна выполняться после основного поведения target-процедуры.",
    notes: [
      "Подходит для пост-обработки и добивки состояния после ванильного кода.",
      "Важно понимать конкретную call chain, чтобы after hook происходил в нужный момент.",
    ],
    example: `hook = project.after_hook("some_proc")
hook.say(Speaker.NANAKO, "Теперь сработал пост-этап.")`,
    result: "Возвращает Procedure для target_hookafter.",
  },
  {
    id: "procedure-say",
    name: "Procedure.say",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.say(message) или proc.say(speaker, text, ...)",
    summary: "Высокоуровневый helper для показа диалога. Сам открывает окно, показывает message и закрывает окно.",
    why: "Это самый удобный способ вставить короткую реплику, не думая каждый раз о OPEN_MSG_WIN/MSG/CLOSE_MSG_WIN.",
    notes: [
      "Можно передать готовый Message или пару speaker + text.",
      "При варианте speaker + text библиотека сама создаёт временный message block.",
      "Если speaker — Character.YOSUKE, стандартный portrait добавится автоматически.",
      "Для help/tutorial popup используй Procedure.help(...), потому что HELP_MSG не открывает обычное окно диалога.",
    ],
    example: `hook.say(Character.YOSUKE, "Привет. Этот мод реально вызвался утром.")`,
    result: "Добавляет в процедуру вызовы открытия окна, показа message и закрытия окна.",
  },
  {
    id: "procedure-call",
    name: "Procedure.call",
    category: "hooks",
    section: "hooks",
    level: "standard",
    signature: "proc.call(function, *args)",
    summary: "Прямой вызов native FlowScript-функции.",
    why: "Нужен, когда библиотека ещё не имеет готового helper для конкретного native-вызова или когда ты осознанно работаешь на более низком уровне.",
    notes: [
      "В beginner доступны только проверенные common-calls; редкие вызовы требуют standard.",
      "Хороший пример — SAVE_ASK, STOP_BGM и другие нативные функции игры.",
    ],
    example: `hook.call("STOP_BGM", 30)
hook.call("SAVE_ASK", 3)`,
    result: "Добавляет строку вида FUNCTION(arg1, arg2); в generated flow.",
  },
  {
    id: "call-original",
    name: "Procedure.call_original",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.call_original()",
    summary: "Вызывает оригинальную процедуру изнутри hook-кода.",
    why: "Нужен, когда hook должен добавить своё поведение, но не ломать ванильную логику полностью.",
    notes: [
      "Для replace_hook это особенно важно: оригинал не вызывается автоматически.",
      "В generated flow метод обращается к *_unhooked варианту оригинальной процедуры.",
    ],
    example: `hook = project.replace_hook("everymorning")
hook.call_original()`,
    result: "Добавляет вызов исходной процедуры в правильной unhooked-форме.",
  },
  {
    id: "procedure-if",
    name: "Procedure.if_",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "with proc.if_(condition): ...",
    summary: "Создаёт FlowScript-блок if (...) { ... } через Python context manager.",
    why: "Это основной способ писать условную логику без ручной работы с фигурными скобками и raw code.",
    notes: [
      "Лучше всего работает с helpers вроде bitChk(), dateChk(), checkTimeSpan() и var(...).",
      "Raw string conditions считаются standard-режимом.",
    ],
    example: `with hook.if_(bitChk(done) == 0):
    hook.say(Speaker.NANAKO, "Это происходит только один раз.")`,
    result: "Рендерит полноценный if-блок в generated flow.",
  },
  {
    id: "procedure-sel",
    name: "Procedure.sel",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: 'proc.sel(variable, selection, *, declare="int")',
    summary: "Показывает selection block и сохраняет индекс выбора игрока в переменную.",
    why: "Используй вместе с Selection, когда мод должен реагировать на выбор пользователя.",
    notes: [
      "Индексы опций начинаются с нуля.",
      "Потом индекс можно сравнить через var(variable) == 0, 1 и так далее.",
    ],
    example: `proc.sel("choice", choices)
with proc.if_(var("choice") == 0):
    proc.say(Speaker.NANAKO, "Выбран первый вариант.")`,
    result: "В generated flow создаёт присваивание переменной через SEL(...).",
  },
  {
    id: "procedure-bit-on",
    name: "Procedure.bit_on",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.bit_on(bit)",
    summary: "Включает bit через BIT_ON(...).",
    why: "Используй, когда мод должен зафиксировать факт того, что кусок логики уже был выполнен.",
    notes: [
      "Обычно применяется после первой реплики, первого выбора или первой выдачи help-сообщения.",
      "Есть алиасы set_bit() и setBit().",
    ],
    example: `hook.bit_on(shown)`,
    result: "Добавляет вызов BIT_ON(...) в generated flow.",
  },
  {
    id: "procedure-bit-off",
    name: "Procedure.bit_off",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.bit_off(bit)",
    summary: "Выключает bit через BIT_OFF(...).",
    why: "Нужен, когда состояние мода должно быть сброшено или когда сценарий повторно открывает ветку поведения.",
    notes: [
      "Есть алиасы clear_bit() и clearBit().",
      "По смыслу часто идёт парой с bitChk(...).",
    ],
    example: `proc.bit_off(done)`,
    result: "Добавляет вызов BIT_OFF(...) в generated flow.",
  },
  {
    id: "message-line",
    name: "Message.line",
    category: "messages",
    section: "messages",
    level: "both",
    signature: "message.line(text, *, wait=True, newline=True, auto_wrap=True, wrap_width=40, max_lines=3, ...)",
    summary: "Добавляет обычную строку в MessageScript-блок с автоматическим экранированием и стандартными тегами.",
    why: "Это главный способ наполнить message block читаемым текстом.",
    notes: [
      "wait=True добавляет [w], newline=True добавляет финальный [n]. Для переноса внутри текста используй обычный Python \\n или line_break().",
      "auto_wrap=True переносит длинный текст по словам: 40 видимых символов на строку и максимум 3 строки на страницу.",
      "first_name(), last_name() и msg_var(...) считаются как 8 символов, потому что реальное значение подставит игра.",
      "Для более осторожного окна можно передать wrap_width=35; для ручной разметки можно передать auto_wrap=False.",
      "Если speaker задан как Character.YOSUKE, стандартный портрет добавится автоматически. Для нестандартного выражения можно передать bustup явно.",
    ],
    example: `msg.line("Сегодня ты тестируешь очень длинную реплику, и библиотека сама перенесёт её на новую строку.")`,
    result: "Дополняет message block одной или несколькими страницами [s]...[w][e], если текст длиннее трёх строк.",
  },
  {
    id: "auto-wrap-parameters",
    name: "auto_wrap / wrap_width / max_lines",
    category: "messages",
    section: "messages",
    level: "both",
    signature: "message.line(..., auto_wrap=True, wrap_width=40, max_lines=3)",
    summary: "Настраивает автоматический перенос текста внутри диалогового окна.",
    why: "Нужен, чтобы пользователь не считал вручную, где ставить [n], особенно когда в строке есть first_name(), last_name() или msg_var(...).",
    notes: [
      "Дефолт 40 выбран по замеру оригинальных .msg: около p95 визуальных строк имеют длину 40 символов или меньше.",
      "Если интерфейс, портрет или русский шрифт требуют запаса, ставь wrap_width=35.",
      "max_lines=3 не даёт одному окну вылезти за высоту textbox: лишний текст уйдёт на следующую страницу сообщения.",
    ],
    example: `msg.line(
    f"Привет, {first_name()}. Это длинная проверочная реплика.",
    wrap_width=35,
)`,
    result: "Библиотека сама вставит [n] и создаст следующую страницу, если строк стало больше трёх.",
  },
  {
    id: "message-raw-line",
    name: "Message.raw_line",
    category: "messages",
    section: "messages",
    level: "standard",
    signature: "message.raw_line(text)",
    summary: "Добавляет raw MessageScript-строку без автоматических [n], [w] и без экранирования.",
    why: "Нужно только тогда, когда ты сознательно хочешь писать нативные теги MessageScript вручную.",
    notes: [
      "Это более опасный путь, потому что библиотека перестаёт защищать тебя от ошибок в разметке.",
    ],
    example: `msg.raw_line("[s][clr 1]Ручной теговый текст[e]")`,
    result: "Вставляет текст как есть в тело message block.",
  },
  {
    id: "selection-option",
    name: "Selection.option",
    category: "messages",
    section: "messages",
    level: "both",
    signature: "selection.option(text)",
    summary: "Добавляет один вариант в selection block.",
    why: "Используй, когда строишь меню выбора для игрока.",
    notes: [
      "Порядок option(...) определяет индекс, который потом вернёт SEL(...).",
    ],
    example: `choices.option("Да, продолжаем")
choices.option("Нет, вернёмся позже")`,
    result: "Дополняет Selection новым пунктом.",
  },
  {
    id: "varchk",
    name: "var",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "var(name)",
    summary: "Создаёт ссылку на переменную FlowScript для сравнений в условиях.",
    why: "Нужен после proc.sel(...) или assign_call(...), когда ты хочешь проверить переменную через Python-подобное выражение.",
    notes: [
      "Обычно используется как var('choice') == 0.",
    ],
    example: `with proc.if_(var("choice") == 0):
    proc.say(Speaker.NANAKO, "Выбран первый пункт.")`,
    result: "Рендерит обращение к имени переменной в generated expression.",
  },
  {
    id: "bitchk",
    name: "bitChk",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "bitChk(bit)",
    summary: "Helper для проверки битов в читабельной форме.",
    why: "Один из самых частых helpers в библиотеке. Почти любой сюжетный мод использует проверки bits.",
    notes: [
      "Обычно сравнивается с нулём или единицей.",
      "Рендерит native-вызов BIT_CHK(...).",
    ],
    example: `with hook.if_(bitChk(done) == 0):
    hook.say(Speaker.NANAKO, "Это первый запуск.")`,
    result: "Рендерит BIT_CHK(bit) как expression.",
  },
  {
    id: "biton",
    name: "bitOn",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "bitOn(bit)",
    summary: "Expression helper для BIT_ON(...).",
    why: "Используется, когда ты хочешь эмитить включение bit как выражение, а не только через метод Procedure.bit_on(...).",
    notes: [
      "Обычно применяется с proc.emit(bitOn(done)).",
    ],
    example: `proc.emit(bitOn(done))`,
    result: "Рендерит statement BIT_ON(bit);",
  },
  {
    id: "bitoff",
    name: "bitOff",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "bitOff(bit)",
    summary: "Expression helper для BIT_OFF(...).",
    why: "Полезен, если ты предпочитаешь строить действия через emit(...) и expression helpers.",
    notes: [
      "Функционально совпадает по смыслу с Procedure.bit_off(...).",
    ],
    example: `proc.emit(bitOff(done))`,
    result: "Рендерит statement BIT_OFF(bit);",
  },
  {
    id: "datechk",
    name: "dateChk",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "dateChk(month, day)",
    summary: "Проверка конкретной игровой даты.",
    why: "Используй, когда событие должно происходить в строго определённый день календаря.",
    notes: [
      "Обычно сравнивается с 1, если дата совпадает.",
    ],
    example: `with hook.if_(dateChk(4, 11) == 1):
    hook.say(Speaker.NANAKO, "Сегодня особая дата.")`,
    result: "Рендерит DATE_CHK(month, day).",
  },
  {
    id: "checktimespan",
    name: "checkTimeSpan",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "checkTimeSpan(start_month, start_day, end_month, end_day)",
    summary: "Проверка диапазона игровых дат.",
    why: "Полезно для сезонных и временных модов, которые должны действовать не один день, а промежуток времени.",
    notes: [
      "Чаще всего сравнивается с 1.",
    ],
    example: `with hook.if_(checkTimeSpan(4, 1, 5, 6) == 1):
    hook.say(Speaker.NANAKO, "Сейчас активен диапазон дат.")`,
    result: "Рендерит CHECK_TIME_SPAN(...).",
  },
  {
    id: "timeofday",
    name: "timeOfDay",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "timeOfDay()",
    summary: "Короткий helper для проверки текущей части дня.",
    why: "Используй вместе с TimeOfDay, когда поведение должно отличаться утром, днём, вечером и так далее.",
    notes: [
      "Внутри рендерит GET_TIME_OF_DAY().",
    ],
    example: `with hook.if_(timeOfDay() == TimeOfDay.DAY):
    hook.say(Speaker.NANAKO, "Это только днём.")`,
    result: "Рендерит GET_TIME_OF_DAY() как expression.",
  },
  {
    id: "gettimeofday",
    name: "getTimeOfDay",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "getTimeOfDay()",
    summary: "Полный helper для получения текущей части дня.",
    why: "По смыслу близок к timeOfDay(). Оба варианта удобны для читаемых сравнений.",
    notes: [
      "Обычно используется как getTimeOfDay() == TimeOfDay.EVENING.",
    ],
    example: `with hook.if_(getTimeOfDay() == TimeOfDay.EVENING):
    hook.say(Speaker.NANAKO, "Это срабатывает вечером.")`,
    result: "Рендерит GET_TIME_OF_DAY() как expression.",
  },
  {
    id: "getcnt",
    name: "getCnt",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "getCnt(index)",
    summary: "Читает значение игрового счётчика по индексу.",
    why: "Нужен для продвинутых условий, когда логика завязана не на bits, а на counters.",
    notes: [
      "Работает как expression и обычно сравнивается с числом.",
    ],
    example: `with hook.if_(getCnt(105) > 3):
    hook.say(Speaker.NANAKO, "Счётчик уже достаточно велик.")`,
    result: "Рендерит GET_CNT(index).",
  },
  {
    id: "setcnt",
    name: "setCnt",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "setCnt(index, value)",
    summary: "Записывает значение в игровой счётчик.",
    why: "Нужен, когда мод должен менять счётчик напрямую.",
    notes: [
      "Часто используется вместе с getCnt().",
    ],
    example: `proc.emit(setCnt(105, 2))`,
    result: "Рендерит statement SET_CNT(index, value);",
  },
  {
    id: "socialstatlevel",
    name: "socialStatLevel",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "socialStatLevel(stat)",
    summary: "Проверка уровня social stat через читабельный helper.",
    why: "Используй, если мод зависит от Courage, Knowledge, Diligence и других социальных параметров.",
    notes: [
      "Лучше использовать вместе с именованными значениями SocialStat.",
    ],
    example: `with hook.if_(socialStatLevel(SocialStat.COURAGE) >= 3):
    hook.say(Speaker.NANAKO, "У тебя достаточно Courage.")`,
    result: "Рендерит GET_SOCIAL_STAT_LEVEL(...).",
  },
  {
    id: "callevent",
    name: "callEvent",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "callEvent(event, minor=None, sub=0)",
    summary: "Готовый helper для запуска event script.",
    why: "Нужен, когда мод должен перевести игру в другой event-контекст.",
    notes: [
      "Можно передавать EventId или raw числовые параметры.",
    ],
    example: `proc.emit(callEvent(5, 12, 0))`,
    result: "Рендерит statement CALL_EVENT(...);",
  },
  {
    id: "callfield",
    name: "callField",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "callField(field_major, room, entrance, mode)",
    summary: "Helper для перехода в field script или другую field-локацию.",
    why: "Используй, когда мод должен переносить игрока в другую карту или безопасно перестраивать маршрут полевого сценария.",
    notes: [
      "Можно работать как с FieldId, так и с аргументами native-вызова.",
    ],
    example: `proc.emit(callField(7, 2, 1, 0))`,
    result: "Рендерит statement CALL_FIELD(...);",
  },
  {
    id: "openmsg",
    name: "openMsg",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "openMsg()",
    summary: "Expression helper для OPEN_MSG_WIN().",
    why: "Полезен для ручной сборки message-последовательности, если say(...) тебе не подходит.",
    notes: [
      "Чаще всего пользоваться say(...) проще.",
    ],
    example: `proc.emit(openMsg())`,
    result: "Рендерит OPEN_MSG_WIN();",
  },
  {
    id: "closemsg",
    name: "closeMsg",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "closeMsg()",
    summary: "Expression helper для CLOSE_MSG_WIN().",
    why: "Нужен, когда ты собираешь message-window flow вручную.",
    notes: [
      "Чаще всего идёт парой с openMsg().",
    ],
    example: `proc.emit(closeMsg())`,
    result: "Рендерит CLOSE_MSG_WIN();",
  },
  {
    id: "helpmsg",
    name: "helpMsg",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "helpMsg(message)",
    summary: "Expression helper для HELP_MSG(...).",
    why: "Используй, когда мод должен показать help-style окно, а не обычный диалог.",
    notes: [
      "Альтернатива — proc.help(...), если нужен более высокий уровень удобства.",
    ],
    example: `proc.emit(helpMsg(HELP_ID))`,
    result: "Рендерит HELP_MSG(message);",
  },
  {
    id: "titledhelpmsg",
    name: "titledHelpMsg",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "titledHelpMsg(title_id, message_id)",
    summary: "Expression helper для TITLED_HELP_MSG(...).",
    why: "Нужен, когда игре требуется help-окно с отдельным заголовком.",
    notes: [
      "Подходит для экранов объяснения механик и вводных уведомлений.",
    ],
    example: `proc.emit(titledHelpMsg(TITLE_HELP, BODY_MSG))`,
    result: "Рендерит TITLED_HELP_MSG(...);",
  },
  {
    id: "rawexpr",
    name: "rawExpr",
    category: "expressions",
    section: "expressions",
    level: "standard",
    signature: "rawExpr(code)",
    summary: "Позволяет вставить raw expression-код, если helper для нужной формы ещё не существует.",
    why: "Нужен как аварийный выход для advanced-авторов, когда библиотека ещё не покрывает специфическую native-конструкцию.",
    notes: [
      "Новичку лучше избегать этого инструмента.",
      "Raw expressions намеренно считаются standard-режимом.",
    ],
    example: `with hook.if_(rawExpr("SOME_NATIVE_CHECK() == 1")):
    hook.say(Speaker.NANAKO, "Raw expression сработал.")`,
    result: "Рендерит переданный код как условное expression.",
  },
  {
    id: "callexpr",
    name: "callExpr",
    category: "expressions",
    section: "expressions",
    level: "standard",
    signature: "callExpr(function, *args)",
    summary: "Строит вызов native-функции как expression-объект.",
    why: "Полезен, когда нужен expression-уровень, но у библиотеки ещё нет отдельного helper с красивым именем.",
    notes: [
      "По смыслу это более структурированный вариант по сравнению с rawExpr().",
    ],
    example: `with hook.if_(callExpr("GET_CNT", 10) > 3):
    hook.say(Speaker.NANAKO, "Проверка через callExpr прошла.")`,
    result: "Возвращает CallExpr для условий или proc.emit(...).",
  },
  {
    id: "speaker",
    name: "Speaker",
    category: "enums",
    section: "enums",
    level: "both",
    signature: "Speaker.NANAKO, Speaker.YOSUKE, ...",
    summary: "Набор читаемых имён говорящих персонажей для message и say(...).",
    why: "Делает код понятнее, чем сырые строковые имена speaker tags.",
    notes: [
      "Особенно удобно в beginner-режиме и в примерах обучения.",
    ],
    example: `hook.say(Speaker.NANAKO, "Добро пожаловать домой.")`,
    result: "Подставляет корректное имя speaker в generated message block.",
  },
  {
    id: "character",
    name: "Character",
    category: "enums",
    section: "enums",
    level: "both",
    signature: "Character.YOSUKE, Character.YOSUKE.with_name(...)",
    summary: "Набор персонажей с именем speaker и стандартным bustup-портретом.",
    why: "Позволяет писать смысловой код без запоминания сырых [bup character expression costume position] чисел.",
    notes: [
      "Character.YOSUKE автоматически даёт speaker Yosuke и портрет [bup 2 1 65535 1].",
      "Можно передавать Character.YOSUKE прямо в project.message(...) или proc.say(...).",
      "with_name(...) сохраняет портрет, но меняет видимое имя. Это удобно для фанатских переводов.",
      "portrait(expression_id=...) позволяет сменить выражение лица без ручного character_id.",
      "Низкоуровневый Bustup(...) остаётся доступен для редких или нестандартных портретов.",
    ],
    example: `yosuke = Character.YOSUKE.with_name("Fsul> %aoanura")
msg = project.message("MOD_YOSUKE", speaker=yosuke)
msg.line("Mpe rabptaft!")`,
    result: "Создаёт сообщение с именем Йоске и его стандартным портретом без ручных bustup-id.",
  },
  {
    id: "timeofday-enum",
    name: "TimeOfDay",
    category: "enums",
    section: "enums",
    level: "both",
    signature: "TimeOfDay.DAY, TimeOfDay.EVENING, ...",
    summary: "Перечисление частей дня для читаемых сравнений.",
    why: "Сильно улучшает читаемость условий по времени дня.",
    notes: [
      "Обычно используется с timeOfDay() или getTimeOfDay().",
    ],
    example: `with hook.if_(timeOfDay() == TimeOfDay.DAY):
    hook.say(Speaker.NANAKO, "Это дневная ветка.")`,
    result: "Даёт именованное значение вместо магического числа.",
  },
  {
    id: "socialstat-enum",
    name: "SocialStat",
    category: "enums",
    section: "enums",
    level: "both",
    signature: "SocialStat.COURAGE, SocialStat.KNOWLEDGE, ...",
    summary: "Перечисление социальных характеристик героя.",
    why: "Используется вместе с socialStatLevel(...) для наглядных условий.",
    notes: [
      "Позволяет избегать неочевидных числовых идентификаторов stat-системы.",
    ],
    example: `with hook.if_(socialStatLevel(SocialStat.COURAGE) >= 3):
    hook.say(Speaker.NANAKO, "Требование по Courage выполнено.")`,
    result: "Даёт именованный social stat identifier.",
  },
  {
    id: "bit-helper",
    name: "bit",
    category: "enums",
    section: "enums",
    level: "both",
    signature: "bit(value, *, name=None, reason=None, safe=False)",
    summary: "Создаёт BitId вручную из числа, если ты уже знаешь конкретный bit и хочешь дать ему имя.",
    why: "Полезно для работы с уже существующими bits игры или с заранее выбранными mod bits.",
    notes: [
      "Для новых пользовательских bits чаще удобнее project.reserve_bit(...).",
    ],
    example: `MOD_DONE = bit(9100, name="MOD_DONE", reason="tutorial example", safe=True)`,
    result: "Возвращает BitId, пригодный для bitChk(), bit_on() и других helpers.",
  },
  {
    id: "eventid",
    name: "EventId",
    category: "enums",
    section: "enums",
    level: "both",
    signature: "EventId(major, minor, sub=0)",
    summary: "Именованный контейнер для event IDs.",
    why: "Нужен, когда ты хочешь хранить событие как объект, а не как россыпь чисел.",
    notes: [
      "Удобен вместе с callEvent(...).",
    ],
    example: `intro_event = EventId(5, 12, 0)
proc.emit(callEvent(intro_event))`,
    result: "Хранит event major/minor/sub в читаемом виде.",
  },
  {
    id: "fieldid",
    name: "FieldId",
    category: "enums",
    section: "enums",
    level: "both",
    signature: "FieldId(field_major, room, entrance, mode=0)",
    summary: "Именованный контейнер для field-переходов.",
    why: "Удобен, когда мод многократно работает с одной и той же локацией или точкой входа.",
    notes: [
      "Хорошо сочетается с callField(...) и Procedure.call_field(...).",
    ],
    example: `shopping_district = FieldId(7, 2, 1, 0)
proc.emit(callField(shopping_district))`,
    result: "Хранит field arguments в структурированной форме.",
  },
  {
    id: "beginner-const",
    name: "BEGINNER",
    category: "core",
    section: "project",
    level: "both",
    signature: "BEGINNER",
    summary: "Экспортированная константа safety-режима beginner.",
    why: "Можно использовать вместо строкового литерала, если хочешь явно опираться на API-константу.",
    notes: [
      "Строка 'beginner' тоже поддерживается.",
    ],
    example: `project = P4GProject("hello", source=SCRIPT, safety=BEGINNER)`,
    result: "Даёт строковое значение режима beginner.",
  },
  {
    id: "standard-const",
    name: "STANDARD",
    category: "core",
    section: "project",
    level: "both",
    signature: "STANDARD",
    summary: "Экспортированная константа safety-режима standard.",
    why: "Подходит, если хочешь использовать символическое имя вместо строкового литерала.",
    notes: [
      "В стандартном режиме доступны и beginner-helpers, и более низкоуровневые инструменты.",
    ],
    example: `project = P4GProject("field_patch", source=SCRIPT, safety=STANDARD)`,
    result: "Даёт строковое значение режима standard.",
  },
  {
    id: "workspace-analyzer",
    name: "WorkspaceAnalyzer",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "WorkspaceAnalyzer.load(...) / analyzer.procedures_named(...) / analyzer.procedure_report(...)",
    summary: "Инструмент анализа decompiled workspace: процедуры, usages, message IDs и другие связи.",
    why: "Когда мод не срабатывает, analyzer помогает понять, существует ли нужная процедура, где она используется и какой call chain к ней ведёт.",
    notes: [
      "Это уже не beginner-сценарий, а инженерный инструмент исследования оригинальных скриптов.",
    ],
    example: `analyzer = WorkspaceAnalyzer.load(workspace_path)
report = analyzer.procedure_report("f007.flow", "call_lmap")
print(report)`,
    result: "Позволяет исследовать оригинальные скрипты и связи между процедурами.",
  },
  {
    id: "run-doctor",
    name: "run_doctor",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "run_doctor(...)",
    summary: "Запускает встроенные проверки проекта и окружения.",
    why: "Полезен, когда нужно быстро получить диагностику по сборке, source и потенциальным ошибкам конфигурации.",
    notes: [
      "Подходит как предварительный health-check перед сложной отладкой.",
    ],
    example: `report = run_doctor(project=project)
print(report)`,
    result: "Возвращает DoctorReport с результатами проверок.",
  },
  {
    id: "analyze-conflicts",
    name: "analyze_project_conflicts",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "analyze_project_conflicts(...)",
    summary: "Проверяет конфликтующие ссылки и потенциальные пересечения с другими скриптами.",
    why: "Нужен, когда проект уже стал больше и важно понять, не лезет ли мод в занятую область bits, message IDs или hook-зон.",
    notes: [
      "Особенно полезно, если ты работаешь не в одиночку или строишь несколько модификаций сразу.",
    ],
    example: `report = analyze_project_conflicts(project, analyzer=analyzer)
print(report)`,
    result: "Возвращает ConflictReport.",
  },
  {
    id: "build-project-file",
    name: "build_project_file",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "build_project_file(path, ...)",
    summary: "Утилита для сборки проекта из отдельного Python-файла через библиотечный API.",
    why: "Подходит для автоматизации, batch-сборок и внешних инструментов поверх pyFlowCompile.",
    notes: [
      "Это уже вспомогательный engineering API, а не первый пользовательский сценарий.",
    ],
    example: `result = build_project_file("examples/mod_project.py")
print(result.bf_path)`,
    result: "Возвращает BuildResult.",
  },
  {
    id: "resolve-compiler-path",
    name: "bundled_compiler_path / resolve_compiler_path",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "bundled_compiler_path() / resolve_compiler_path(...)",
    summary: "Вспомогательные функции для определения пути к компилятору AtlusScriptTools.",
    why: "Полезно для тех случаев, когда ты строишь свою автоматизацию или хочешь понять, какой compiler binary реально используется.",
    notes: [
      "Обычному пользователю библиотеки это чаще всего не нужно — Build() берёт путь сам.",
    ],
    example: `compiler = bundled_compiler_path()
print(compiler)`,
    result: "Возвращает путь к compiler executable или вычисляет его по конфигурации.",
  },
];
const p4gProjectRef = referenceItems.find((item) => item.id === "p4gproject");
if (p4gProjectRef) {
  p4gProjectRef.notes.unshift("Для типовых сценариев теперь есть более короткие constructors: patch_script(...), patch_field_script(...), new_script(...), new_field_script(...). Их стоит считать основным beginner-путём.");
  p4gProjectRef.result = "Возвращает объект проекта, на котором дальше вызываются message(), procedure(), hooks и Build(). Для самых частых сценариев можно вообще стартовать с classmethod-конструктора проекта.";
}

const selectionRef = referenceItems.find((item) => item.id === "selection-method");
if (selectionRef) {
  selectionRef.notes.push("Если тебе не нужен отдельный reusable Selection object, для простого меню чаще быстрее использовать Procedure.ask(...). ");
}

const ifRef = referenceItems.find((item) => item.id === "procedure-if");
if (ifRef) {
  ifRef.notes.push("Для самых частых проверок появились ещё более короткие wrappers: when_bit_clear(...), when_bit_set(...), when_time(...), during(...), once(...). ");
}

referenceItems.push(
  {
    id: "project-new-script",
    name: "P4GProject.new_script",
    category: "core",
    section: "project",
    level: "both",
    signature: 'P4GProject.new_script(name, *, target=None, safety="standard", ...)',
    summary: "Короткий constructor для нового standalone script без ручного Empty(...).",
    why: "Используй, когда хочешь создать новый script container и не тратить код на отдельный source helper.",
    notes: [
      "Подходит для create mode.",
      "Если target не указан, build всё равно возможен, но packaging и установка будут менее понятными.",
      "Для field и event scripts есть ещё более удобные new_field_script(...) и new_event_script(...).",
    ],
    example: `project = P4GProject.new_script(
    "custom_script",
    target="data_e.cpk/field/script/custom_script.bf",
    safety="beginner",
)`,
    result: "Возвращает готовый P4GProject в create mode.",
  },
  {
    id: "project-patch-script",
    name: "P4GProject.patch_script",
    category: "core",
    section: "project",
    level: "both",
    signature: 'P4GProject.patch_script(name, original_bf, *, target=None, import_path=None, ...)',
    summary: "Короткий constructor для patch mode без ручного BF(...).",
    why: "Полезен, когда у тебя уже есть original .bf и ты хочешь сразу получить проект для hook-сборки.",
    notes: [
      "Это универсальный patch constructor.",
      "Для field scripts чаще ещё удобнее patch_field_script(...), потому что он сам строит field target path.",
    ],
    example: `project = P4GProject.patch_script(
    "hello_scheduler",
    Path(__file__).with_name("scheduler_01.bf"),
    target="data_e/scheduler/scheduler_01.bf",
    import_path="original_scheduler_01.bf",
    safety="beginner",
)`,
    result: "Возвращает P4GProject в patch mode с уже настроенным BF source.",
  },
  {
    id: "project-new-field-script",
    name: "P4GProject.new_field_script",
    category: "core",
    section: "project",
    level: "both",
    signature: 'P4GProject.new_field_script(name, script_name, *, archive="data_e.cpk", ...)',
    summary: "Создаёт новый field-script project и сам подставляет стандартный field target path.",
    why: "Это лучший create-mode путь для новичка, когда хочется писать мод для field script и не думать о layout пути вручную.",
    notes: [
      "script_name — это логическое имя script container, например f007 или custom_field_script.",
      "По умолчанию target будет data_e.cpk/field/script/<script_name>.bf.",
    ],
    example: `project = P4GProject.new_field_script(
    "dialogue_example",
    "dialogue_example",
    safety="beginner",
)`,
    result: "Возвращает P4GProject в create mode с field target path.",
  },
  {
    id: "project-patch-field-script",
    name: "P4GProject.patch_field_script",
    category: "core",
    section: "project",
    level: "both",
    signature: 'P4GProject.patch_field_script(name, script_name, original_bf, *, import_path=None, ...)',
    summary: "Главный короткий constructor для patch-модов по обычным field scripts вроде f007.",
    why: "Это лучший beginner-friendly путь для реального P4G hook-мода: ты указываешь script name и original .bf, а библиотека сама строит типовой target path.",
    notes: [
      "Особенно полезен для f007, f011, comuXX и других полевых скриптов.",
      "Убирает одну из самых частых ошибок новичка: ручной target path с опечаткой.",
    ],
    example: `project = P4GProject.patch_field_script(
    "nanako_evening_follow_along",
    "f007",
    Path(__file__).with_name("f007.bf"),
    import_path="original_f007.bf",
    safety="beginner",
)`,
    result: "Возвращает P4GProject в patch mode, готовый к replace_hook(...) или soft_hook(...).",
  },
  {
    id: "field-target",
    name: "field_target",
    category: "core",
    section: "project",
    level: "both",
    signature: 'field_target(script_name, *, archive="data_e.cpk")',
    summary: "Строит стандартный target path для field script.",
    why: "Нужен, когда хочется явно увидеть или переиспользовать target path, но не печатать его вручную каждый раз.",
    notes: [
      'field_target("f007") -> data_e.cpk/field/script/f007.bf',
      "Полезен и в документации, и в кастомных build-обвязках.",
    ],
    example: `target = field_target("f007")
# -> data_e.cpk/field/script/f007.bf`,
    result: "Возвращает строку target path для field script.",
  },
  {
    id: "field-bf",
    name: "FieldBF",
    category: "core",
    section: "project",
    level: "both",
    signature: 'FieldBF(script_name, path, *, import_path=None, archive="data_e.cpk", copy=True)',
    summary: "Field-специализированный вариант BF(...).",
    why: "Нужен, когда тебе всё ещё нравится явный source object, но не хочется каждый раз вручную писать стандартный field target path.",
    notes: [
      "Возвращает обычный ScriptSource.",
      "Можно передавать в P4GProject(source=...).",
    ],
    example: `SCRIPT = FieldBF(
    "f007",
    Path(__file__).with_name("f007.bf"),
    import_path="original_f007.bf",
)`,
    result: "Возвращает ScriptSource для field patch mode.",
  },
  {
    id: "field-empty",
    name: "FieldEmpty",
    category: "core",
    section: "project",
    level: "both",
    signature: 'FieldEmpty(script_name, *, archive="data_e.cpk")',
    summary: "Field-специализированный вариант Empty(...).",
    why: "Полезен для учебных standalone field scripts, когда нужен явный ScriptSource, но не хочется руками писать target path.",
    notes: [
      "Возвращает обычный ScriptSource.",
      "Полезен там, где класс-метод new_field_script(...) по стилю не подходит.",
    ],
    example: `SCRIPT = FieldEmpty("custom_field_script")`,
    result: "Возвращает ScriptSource для нового field script.",
  },
  {
    id: "procedure-ask",
    name: "Procedure.ask",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: 'proc.ask(variable, *options, name=None, pattern="top", declare="int")',
    summary: "Создаёт selection block, показывает его и сразу возвращает переменную выбора в удобной форме.",
    why: "Это самый короткий путь для обычного меню выбора, когда не нужен отдельный reusable Selection object.",
    notes: [
      "Под капотом создаёт Selection и вызывает SEL(...).",
      "Возвращаемое значение уже можно сравнивать как choice == 0 внутри proc.if_(...).",
    ],
    example: `choice = proc.ask("choice", "Да", "Нет")
with proc.if_(choice == 0):
    proc.say(Speaker.NANAKO, "Выбран первый вариант.")`,
    result: "Добавляет selection в .msg, вызов SEL(...) в .flow и возвращает var(variable).",
  },
  {
    id: "procedure-once",
    name: "Procedure.once",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "with proc.once(done_bit, *, condition=None): ...",
    summary: "Открывает одноразовый блок: проверяет bit и автоматически ставит его в конце успешного выполнения.",
    why: "Это один из самых полезных сокращателей кода для beginner-модов. Не нужно вручную писать и condition, и BIT_ON(...).",
    notes: [
      "Если condition передан, он добавляется к bit guard через &&.",
      "Автоматический BIT_ON(...) пишется только если тело блока завершилось без ошибки на этапе сборки.",
    ],
    example: `with hook.once(done, condition=timeOfDay() == TimeOfDay.EVENING):
    hook.say(Speaker.NANAKO, "Вечерняя сцена сработала один раз.")`,
    result: "Рендерит if-блок с BIT_CHK(done) == 0 и автоматическим BIT_ON(done) внутри него.",
  },
  {
    id: "procedure-during",
    name: "Procedure.during",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "with proc.during(start_month, start_day, end_month, end_day): ...",
    summary: "Короткий wrapper вокруг CHECK_TIME_SPAN(...).",
    why: "Подходит для очень частого P4G-паттерна: действие активно в диапазоне дат, а не в одну конкретную дату.",
    notes: [
      "Внутри использует checkTimeSpan(...) == 1.",
      "Снижает визуальный шум в beginner-коде.",
    ],
    example: `with hook.during(4, 1, 5, 6):
    hook.say(Speaker.NANAKO, "Сейчас активен нужный диапазон дат.")`,
    result: "Рендерит if (CHECK_TIME_SPAN(...) == 1) { ... }.",
  },
  {
    id: "procedure-when-time",
    name: "Procedure.when_time",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "with proc.when_time(TimeOfDay.EVENING): ...",
    summary: "Короткий wrapper для проверки части дня без ручного timeOfDay() == ...",
    why: "Полезен, когда в моде часто встречаются утро/день/вечер и хочется сразу видеть смысл блока, а не полное expression-выражение.",
    notes: [
      "Внутри использует timeOfDay() == slot.",
      "Для нестандартных составных условий по-прежнему можно использовать proc.if_(...).",
    ],
    example: `with hook.when_time(TimeOfDay.EVENING):
    hook.say(Speaker.NANAKO, "Эта реплика только вечером.")`,
    result: "Рендерит if (GET_TIME_OF_DAY() == value) { ... }.",
  },
  {
    id: "procedure-when-bit-clear",
    name: "Procedure.when_bit_clear",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "with proc.when_bit_clear(bit): ...",
    summary: "Короткий wrapper для if (BIT_CHK(bit) == 0).",
    why: "Это очень частый P4G-паттерн, поэтому для новичка проще читать именно готовое имя намерения, а не каждый раз полное expression-условие.",
    notes: [
      "Есть парный helper when_bit_set(...).",
      "Оба helpers по-прежнему регистрируют именованные BitId внутри проекта.",
    ],
    example: `with hook.when_bit_clear(done):
    hook.say(Speaker.NANAKO, "Это произошло впервые.")`,
    result: "Рендерит if (BIT_CHK(bit) == 0) { ... }.",
  },
  {
    id: "procedure-when-bit-set",
    name: "Procedure.when_bit_set",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "with proc.when_bit_set(bit): ...",
    summary: "Короткий wrapper для if (BIT_CHK(bit) == 1).",
    why: "Полезен, когда действие должно происходить только после уже установленного состояния.",
    notes: [
      "Часто используется для ветвлений по уже завершённому этапу мода.",
    ],
    example: `with hook.when_bit_set(done):
    hook.help("Сцена уже была показана раньше.")`,
    result: "Рендерит if (BIT_CHK(bit) == 1) { ... }.",
  },
  {
    id: "procedure-add-yen",
    name: "Procedure.add_yen",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.add_yen(amount)",
    summary: "Высокоуровневый helper для ADD_YEN(...).",
    why: "Часто нужен в наградах, тестовых модах и маленьких сценках, поэтому полезно иметь понятное Python-имя вместо raw native call.",
    notes: [
      "Есть beginner-friendly alias addYen(...).",
    ],
    example: `proc.add_yen(3000)`,
    result: "Рендерит ADD_YEN(amount);",
  },
  {
    id: "procedure-set-item",
    name: "Procedure.set_item",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.set_item(item_id, amount)",
    summary: "Высокоуровневый helper для SET_ITEM(...).",
    why: "Полезен для shop-модов, наград и простых item-driven сцен, где не хочется уходить в raw native call.",
    notes: [
      "Есть alias setItem(...).",
    ],
    example: `proc.set_item(123, 1)`,
    result: "Рендерит SET_ITEM(item_id, amount);",
  },
  {
    id: "procedure-get-item",
    name: "Procedure.get_item",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: 'proc.get_item(variable, item_id, *, declare="int")',
    summary: "Читает GET_ITEM(item_id) в FlowScript-переменную через builder-API.",
    why: "Нужен, когда мод должен проверять количество конкретного предмета, но хочется оставаться в коротком Python-DSL.",
    notes: [
      "Есть alias getItem(...).",
      "Для expression-стиля также есть getItem(item_id) как helper-функция.",
    ],
    example: `proc.get_item("coffeeCount", 123)
with proc.if_(var("coffeeCount") > 0):
    proc.say(Speaker.NANAKO, "У тебя уже есть этот предмет.")`,
    result: "Рендерит присваивание вида int coffeeCount = GET_ITEM(123);",
  },
  {
    id: "procedure-set-msg-var",
    name: "Procedure.set_msg_var",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.set_msg_var(index, value, digits=0)",
    summary: "Заполняет message variable slot через SET_MSG_VAR(...).",
    why: "Нужен, когда текст должен показывать деньги, количество или другое число прямо внутри сообщения.",
    notes: [
      "Есть alias setMsgVar(...).",
    ],
    example: `proc.set_msg_var(0, 3000)
proc.say(Speaker.NANAKO, "Награда подготовлена.")`,
    result: "Рендерит SET_MSG_VAR(index, value, digits);",
  },
  {
    id: "getitem-helper",
    name: "getItem",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "getItem(item_id)",
    summary: "Expression helper для GET_ITEM(item_id).",
    why: "Полезен, когда количество предмета нужно читать именно как expression в условии, а не как отдельное присваивание через Procedure.get_item(...).",
    notes: [
      "Подходит для proc.if_(getItem(123) > 0).",
    ],
    example: `with hook.if_(getItem(123) > 0):
    hook.say(Speaker.NANAKO, "Этот предмет уже есть у игрока.")`,
    result: "Рендерит GET_ITEM(item_id) как expression.",
  },
  {
    id: "setitem-helper",
    name: "setItem",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "setItem(item_id, amount)",
    summary: "Expression helper для SET_ITEM(...).",
    why: "Нужен, если ты строишь действия в expression-стиле через proc.emit(...).",
    notes: [
      "Функционально близок к Procedure.set_item(...).",
    ],
    example: `proc.emit(setItem(123, 1))`,
    result: "Рендерит SET_ITEM(item_id, amount);",
  },
  {
    id: "setmsgvar-helper",
    name: "setMsgVar",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "setMsgVar(index, value, digits=0)",
    summary: "Expression helper для SET_MSG_VAR(...).",
    why: "Полезен, если тебе удобнее работать через emit(...) и готовые CallExpr objects.",
    notes: [
      "Функционально близок к Procedure.set_msg_var(...).",
    ],
    example: `proc.emit(setMsgVar(0, 3000))`,
    result: "Рендерит SET_MSG_VAR(index, value, digits);",
  },
  {
    id: "addyen-helper",
    name: "addYen",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "addYen(amount)",
    summary: "Expression helper для ADD_YEN(...).",
    why: "Полезен в сценариях, где хочется описывать награду через emit(...) или комбинировать её с другими CallExpr helpers.",
    notes: [
      "Функционально близок к Procedure.add_yen(...).",
    ],
    example: `proc.emit(addYen(3000))`,
    result: "Рендерит ADD_YEN(amount);",
  }
);
referenceItems.push(
  {
    id: "project-show-message-before-original",
    name: "P4GProject.show_message_before_original",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "project.show_message_before_original(target, speaker_or_message, text=None, *, condition=None, mode='replace', name=None)",
    summary: "Готовый сценарный helper: показать сообщение в hook, затем вызвать оригинальную процедуру.",
    why: "Это самый частый beginner-паттерн: добавить реплику или диагностическое сообщение и не забыть call_original().",
    notes: [
      "Создаёт hook выбранного target.",
      "Если condition задан, сообщение показывается только внутри этого условия.",
      "В конце всегда вызывает оригинальную процедуру через call_original().",
    ],
    example: `project.show_message_before_original(
    "SCR_ONLY_NPC_YOUSUKE",
    Character.YOSUKE,
    "Partner check.",
    name="MOD_YOSUKE_TEST",
)`,
    result: "Возвращает Procedure созданного hook.",
  },
  {
    id: "project-replace-with-message",
    name: "P4GProject.replace_with_message",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "project.replace_with_message(target, speaker_or_message, text=None, *, condition=None, name=None)",
    summary: "Создаёт replace-hook, который показывает сообщение вместо оригинального поведения.",
    why: "Используй только тогда, когда мод действительно должен заменить ванильную процедуру, а не продолжить её после сообщения.",
    notes: [
      "Этот helper намеренно не вызывает call_original().",
      "Для безопасного добавления реплики чаще лучше show_message_before_original(...).",
    ],
    example: `project.replace_with_message(
    "SOME_TEST_PROC",
    "System",
    "Оригинальная процедура заменена.",
)`,
    result: "Возвращает Procedure созданного replace hook.",
  },
  {
    id: "project-show-help-once",
    name: "P4GProject.show_help_once",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "project.show_help_once(target, message_or_text, done_bit, *, condition=None, mode='replace', name=None)",
    summary: "Показывает HELP_MSG один раз, ставит bit и затем вызывает оригинальную процедуру.",
    why: "Подходит для tutorial/help popup и диагностических уведомлений, которые не должны повторяться бесконечно.",
    notes: [
      "Проверяет BIT_CHK(done_bit) == 0.",
      "После показа help-сообщения вызывает BIT_ON(done_bit).",
      "В конце вызывает оригинальную процедуру.",
    ],
    example: `done = project.reserve_bit("MOD_HELP_SHOWN")
project.show_help_once("everymorning", "Мод загружен.", done)`,
    result: "Возвращает Procedure созданного hook.",
  },
  {
    id: "procedure-help",
    name: "Procedure.help",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.help(message_or_text, *, name=None, wait=True, newline=True, ...)",
    summary: "Высокоуровневый helper для HELP_MSG(...).",
    why: "Используй, когда нужен help/tutorial popup, а не обычное диалоговое окно с OPEN_MSG_WIN и CLOSE_MSG_WIN.",
    notes: [
      "Можно передать готовый Message или обычный текст.",
      "Для обычного диалога используй proc.say(...).",
    ],
    example: `hook.help("Сработал хук: SCR_ONLY_NPC_YOUSUKE", name="MOD_DEBUG_HELP")`,
    result: "Создаёт message block при необходимости и рендерит HELP_MSG(...).",
  },
  {
    id: "procedure-ask-yes-no",
    name: "Procedure.ask_yes_no",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.ask_yes_no(variable='choice', *, yes='Yes', no='No', name=None, declare='int')",
    summary: "Короткий yes/no wrapper поверх Procedure.ask(...).",
    why: "Подходит для самого частого выбора из двух вариантов без ручного создания Selection.",
    notes: [
      "Возвращает var(variable), поэтому результат можно сразу сравнивать в proc.if_(choice == 0).",
      "Индекс 0 соответствует yes, индекс 1 соответствует no.",
    ],
    example: `choice = proc.ask_yes_no(yes="Да", no="Нет")
with proc.if_(choice == 0):
    proc.say("System", "Игрок выбрал Да.")`,
    result: "Создаёт selection, вызывает SEL(...) и возвращает expression переменной выбора.",
  }
);
const levelLabels = {
  beginner: "Beginner",
  both: "Beginner + Standard",
  standard: "Standard",
  tool: "Tooling",
};

referenceItems.push(
  {
    id: "first-name-helper",
    name: "first_name",
    category: "messages",
    section: "messages",
    level: "both",
    signature: "first_name()",
    summary: "Возвращает MessageScript-тег [fName] для имени героя, введённого игроком.",
    why: "Используй, когда персонаж должен обратиться к протагонисту по имени. Это тот же механизм, который встречается в оригинальном comu00.msg: текст хранит [fName], а игра заменяет тег при показе сообщения.",
    notes: [
      "Библиотека сохраняет этот безопасный тег автоматически, поэтому для first_name() не нужно отключать экранирование вручную.",
      "Для фанатского перевода можно прогнать строку через translate.py: он сохраняет tags внутри квадратных скобок, а библиотека не превратит [fName] в обычный текст.",
    ],
    example: `hook.say(
    Speaker.NANAKO,
    f"Hello, {first_name()}. Great script!",
)`,
    result: "В .msg остаётся [fName], и игра подставляет имя игрока во время показа сообщения.",
  },
  {
    id: "last-name-helper",
    name: "last_name",
    category: "messages",
    section: "messages",
    level: "both",
    signature: "last_name()",
    summary: "Возвращает MessageScript-тег [lName] для фамилии героя.",
    why: "Нужен для японского стиля обращения или любых строк, где персонаж должен обратиться к игроку по фамилии.",
    notes: [
      "Как и first_name(), сохраняется автоматически внутри обычной строки.",
      "Можно комбинировать: f'{last_name()} {first_name()}'.",
    ],
    example: `hook.say(Speaker.NANAKO, f"Welcome back, {last_name()}.")`,
    result: "В .msg остаётся [lName].",
  },
  {
    id: "msg-var-helper",
    name: "msg_var",
    category: "messages",
    section: "messages",
    level: "both",
    signature: "msg_var(index)",
    summary: "Возвращает MessageScript-тег [var N] для значения, подготовленного через SET_MSG_VAR.",
    why: "Используй, когда в сообщении нужно показать число, счётчик или другое значение из message variable slot.",
    notes: [
      "Перед показом сообщения slot должен быть заполнен через proc.set_msg_var(...) или setMsgVar(...).",
      "Библиотека сохраняет msg_var(...) автоматически внутри обычной строки.",
    ],
    example: `proc.set_msg_var(0, 3000)
proc.say(Speaker.NANAKO, f"You have {msg_var(0)} yen.")`,
    result: "В .msg остаётся [var 0], а FlowScript заранее заполняет slot через SET_MSG_VAR.",
  },
  {
    id: "line-break-helper",
    name: "line_break",
    category: "messages",
    section: "messages",
    level: "both",
    signature: "line_break() / new_line()",
    summary: "Возвращает MessageScript-тег [n] для переноса строки внутри одного диалогового окна.",
    why: "Используй, когда реплика длинная и должна быть разбита на две строки без создания отдельного сообщения.",
    notes: [
      "Обычный Python \\n внутри text тоже автоматически превращается в [n].",
      "line_break() удобен, когда хочется явно показать перенос внутри f-string рядом с first_name() или msg_var().",
    ],
    example: `msg.line(f"Hello, {first_name()}.{line_break()}Good script!")`,
    result: "В .msg получится Hello, [fName].[n]Good script!",
  }
);
referenceItems.push(
  {
    id: "project-new-event-script",
    name: "P4GProject.new_event_script",
    category: "core",
    section: "project",
    level: "both",
    signature: 'P4GProject.new_event_script(name, script_name, *, archive="data_e.cpk", ...)',
    summary: "Создаёт новый event-script project и сам подставляет стандартный event target path.",
    why: "Используй, когда нужен новый event script container, а не patch существующего .bf.",
    notes: [
      "Как и любой create-mode script, сам по себе не гарантирует игровой вызов.",
      "Target будет data_e.cpk/event_data/script/<script_name>.bf.",
    ],
    example: `project = P4GProject.new_event_script(
    "custom_event",
    "E999_001A",
    safety="beginner",
)`,
    result: "Возвращает P4GProject в create mode с event target path.",
  },
  {
    id: "project-patch-event-script",
    name: "P4GProject.patch_event_script",
    category: "core",
    section: "project",
    level: "both",
    signature: 'P4GProject.patch_event_script(name, script_name, original_bf, *, import_path=None, ...)',
    summary: "Event-script вариант patch_field_script(...).",
    why: "Нужен, когда мод должен hook-нуть или заменить поведение существующего event script.",
    notes: [
      "Сам строит target path для data_e.cpk/event_data/script/...",
      "Для field scripts используй patch_field_script(...).",
    ],
    example: `project = P4GProject.patch_event_script(
    "aika_restore_patch",
    "E860_065A",
    Path("E860_065A.bf"),
    import_path="original_E860_065A.bf",
)`,
    result: "Возвращает P4GProject в patch mode для event script.",
  },
  {
    id: "event-target",
    name: "event_target",
    category: "core",
    section: "project",
    level: "both",
    signature: 'event_target(script_name, *, archive="data_e.cpk")',
    summary: "Строит стандартный target path для event script.",
    why: "Убирает ручное повторение data_e.cpk/event_data/script/... в build-конфигурациях.",
    notes: [
      'event_target("E860_074A") -> data_e.cpk/event_data/script/E860_074A.bf',
    ],
    example: `target = event_target("E860_074A")`,
    result: "Возвращает строку target path для event script.",
  },
  {
    id: "event-bf",
    name: "EventBF",
    category: "core",
    section: "project",
    level: "both",
    signature: 'EventBF(script_name, path, *, import_path=None, archive="data_e.cpk", copy=True)',
    summary: "Event-специализированный вариант BF(...).",
    why: "Используй, когда хочешь явно создать ScriptSource для patch event script без ручного target path.",
    notes: [
      "Возвращает ScriptSource.",
      "В новых примерах чаще проще P4GProject.patch_event_script(...).",
    ],
    example: `SCRIPT = EventBF("E860_074A", Path("E860_074A.bf"))`,
    result: "Возвращает source для event patch mode.",
  },
  {
    id: "event-empty",
    name: "EventEmpty",
    category: "core",
    section: "project",
    level: "both",
    signature: 'EventEmpty(script_name, *, archive="data_e.cpk")',
    summary: "Event-специализированный вариант Empty(...).",
    why: "Нужен для явного create-mode source под новый event script.",
    notes: [
      "Новый script всё равно должен быть вызван игрой или другим script.",
    ],
    example: `SCRIPT = EventEmpty("E999_001A")`,
    result: "Возвращает source для нового event script.",
  },
  {
    id: "project-write-compile-build",
    name: "project.write / project.compile / project.build",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "project.write(out_dir) / project.compile(out_dir) / project.build(out_dir, ...)",
    summary: "Низкоуровневые шаги сборки, на которых основан beginner-friendly Build(...).",
    why: "Нужны для автоматизации, CI, ручной диагностики и случаев, где нужно получить .flow/.msg без компиляции .bf.",
    notes: [
      "project.write(...) только пишет source-файлы.",
      "project.compile(...) вызывает AtlusScriptCompiler после write(...).",
      "project.build(...) делает полный build pipeline и возвращает BuildResult.",
      "Обычному пользователю чаще достаточно project.Build(...).",
    ],
    example: `flow_path, msg_path = project.write("out")
result = project.build("out", compile_bf=True, debug=True)`,
    result: "Даёт точечный контроль над этапами build pipeline.",
  },
  {
    id: "project-render-methods",
    name: "project.render_flow / project.render_msg",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "project.render_flow() / project.render_msg()",
    summary: "Возвращает generated FlowScript или MessageScript как строку без записи файлов.",
    why: "Полезно для тестов, golden checks и быстрого просмотра результата генерации.",
    notes: [
      "render_flow() требует хотя бы одну procedure.",
      "render_msg() возвращает все messages и selections проекта.",
    ],
    example: `print(project.render_flow())
print(project.render_msg())`,
    result: "Возвращает текст .flow или .msg.",
  },
  {
    id: "project-source-imports",
    name: "project.target / use / import_bf / import_flow / import_msg",
    category: "core",
    section: "project",
    level: "standard",
    signature: "project.target(path), project.use(source), project.import_bf(path), ...",
    summary: "Ручное управление target path и import-файлами generated FlowScript project.",
    why: "Нужно, когда коротких constructors недостаточно или проект собирается нестандартным способом.",
    notes: [
      "В beginner tutorials лучше начинать с patch_field_script(...) или patch_event_script(...).",
      "import_bf(...) добавляет original .bf в generated import(...).",
      "import_flow(...) и import_msg(...) нужны для advanced-компоновки нескольких source-файлов.",
    ],
    example: `project.target("data_e.cpk/field/script/f007.bf")
project.import_bf("original_f007.bf", import_path="original_f007.bf")`,
    result: "Позволяет собрать нестандартную import/target схему.",
  },
  {
    id: "build-project-api",
    name: "build_project / load_project_from_file",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "build_project(project, out_dir, ...) / load_project_from_file(path)",
    summary: "Engineering API для программной сборки проектов без ручного запуска example-файла.",
    why: "Полезно для внешних launchers, batch-сборки и тестов вокруг библиотеки.",
    notes: [
      "load_project_from_file(...) ожидает Python-файл с callable build_project().",
      "build_project_file(...) объединяет загрузку файла и build pipeline.",
    ],
    example: `project = load_project_from_file("examples/my_mod.py")
result = build_project(project, "build/my_mod")`,
    result: "Возвращает P4GProject или BuildResult в зависимости от helper.",
  },
  {
    id: "compiler-types",
    name: "CompilerConfig / CompileResult / BuildResult",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "CompilerConfig(...), CompileResult(...), BuildResult(...) ",
    summary: "Structured result/config объекты build и compile pipeline.",
    why: "Нужны, когда ты пишешь tooling поверх библиотеки и хочешь читать пути, stdout/stderr, warnings и package output программно.",
    notes: [
      "Beginner-код обычно просто печатает result.flow_path/msg_path/bf_path.",
      "CompilerConfig позволяет явно задать library, encoding, hook и debug для compiler layer.",
    ],
    example: `result = project.Build(Debug=True)
print(result.bf_path)`,
    result: "Даёт structured access к результату сборки.",
  },
  {
    id: "bundled-compiler-root",
    name: "bundled_compiler_root",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "bundled_compiler_root()",
    summary: "Возвращает папку bundled AtlusScriptTools, которую использует библиотека.",
    why: "Помогает проверить, откуда берётся compiler и какие tools лежат рядом с библиотекой.",
    notes: [
      "Обычно Build() сам находит bundled compiler.",
    ],
    example: `print(bundled_compiler_root())`,
    result: "Возвращает Path к tools/AtlusScriptTools.",
  },
  {
    id: "procedure-low-level-output",
    name: "Procedure.line / raw / emit / assign_call / return_",
    category: "hooks",
    section: "hooks",
    level: "standard",
    signature: "proc.line(code), proc.raw(code), proc.emit(call), proc.assign_call(var, function, ...), proc.return_()",
    summary: "Низкоуровневые способы писать FlowScript statements напрямую или через CallExpr.",
    why: "Нужны, когда готового beginner-helper ещё нет, но ты понимаешь нативный FlowScript.",
    notes: [
      "raw(...) и raw string paths требуют standard safety.",
      "emit(...) безопаснее raw, если передан CallExpr от typed helper.",
      "assign_call(...) удобен для int value = NATIVE(...);",
      "return_() отключает автоматический final return для procedure.",
    ],
    example: `proc.assign_call("count", "GET_CNT", 10)
proc.emit(bitOn(done))
proc.return_()`,
    result: "Пишет низкоуровневые FlowScript statements.",
  },
  {
    id: "procedure-message-low-level",
    name: "Procedure.open_msg / close_msg / msg / help_msg / titled_help_msg",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.open_msg(), proc.msg(message), proc.close_msg(), proc.help_msg(message), proc.titled_help_msg(message, title_id)",
    summary: "Низкоуровневые message calls, на которых построены proc.say(...) и proc.help(...).",
    why: "Используй, когда нужно вручную контролировать окно сообщения или показать уже созданный Message object.",
    notes: [
      "Для обычной реплики чаще короче proc.say(...).",
      "Для help popup чаще короче proc.help(...).",
    ],
    example: `proc.open_msg()
proc.msg(message)
proc.close_msg()`,
    result: "Рендерит OPEN_MSG_WIN(), MSG(...), CLOSE_MSG_WIN() или HELP_MSG(...).",
  },
  {
    id: "procedure-call-event-field",
    name: "Procedure.call_event / call_field",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.call_event(EventId(...)) / proc.call_field(FieldId(...), safe=False)",
    summary: "Procedure helpers для перехода в event script или field script.",
    why: "Нужны, когда мод должен запустить событие или перенести игрока в другую локацию.",
    notes: [
      "Для raw expression style есть callEvent(...) и callField(...).",
      "call_field(..., safe=True) использует CALL_FIELD_SAFE.",
    ],
    example: `proc.call_event(EventId(860, 74, 0))
proc.call_field(FieldId(7, 2, 1, 0), safe=True)`,
    result: "Рендерит CALL_EVENT(...) или CALL_FIELD/CALL_FIELD_SAFE(...).",
  },
  {
    id: "procedure-aliases",
    name: "Procedure aliases: setBit / clearBit / addYen / setItem / getItem / setMsgVar / callOriginal",
    category: "hooks",
    section: "hooks",
    level: "both",
    signature: "proc.setBit(...), proc.clearBit(...), proc.addYen(...), proc.setItem(...), proc.getItem(...), proc.setMsgVar(...), proc.callOriginal()",
    summary: "Beginner-readable aliases для часто используемых Procedure methods.",
    why: "Позволяют писать код ближе к стилю beginner tutorial без запоминания snake_case вариантов.",
    notes: [
      "Snake_case методы тоже доступны: bit_on, bit_off, add_yen, set_item, get_item, set_msg_var, call_original.",
    ],
    example: `hook.setBit(done)
hook.callOriginal()`,
    result: "Рендерит те же statements, что и snake_case методы.",
  },
  {
    id: "date-timespan",
    name: "Date / TimeSpan",
    category: "expressions",
    section: "expressions",
    level: "both",
    signature: "Date(month, day), TimeSpan(start_month, start_day, end_month, end_day)",
    summary: "Readable wrappers для date-based conditions.",
    why: "Нужны, чтобы условия календаря были понятнее голых DATE_CHK/CHECK_TIME_SPAN вызовов.",
    notes: [
      "Date(...).render_condition() даёт DATE_CHK(...).",
      "TimeSpan(...) хорошо сочетается с proc.when(...).",
    ],
    example: `with proc.when(TimeSpan(4, 1, 5, 6)):
    proc.say("System", "Дата внутри диапазона.")`,
    result: "Рендерит date/time-span condition в FlowScript.",
  },
  {
    id: "expr-types",
    name: "Expr / CallExpr / IdentifierExpr",
    category: "expressions",
    section: "expressions",
    level: "standard",
    signature: "Expr, CallExpr(function, *args), IdentifierExpr(name)",
    summary: "Низкоуровневые expression objects, которые стоят под helpers вроде bitChk(...) и var(...).",
    why: "Обычный пользователь редко создаёт их напрямую, но важно понимать, что Python expression не выполняется, а рендерится в FlowScript.",
    notes: [
      "Expr запрещает использование в обычном Python if, чтобы не спутать build-time и game-time logic.",
      "CallExpr может рендериться и как expression, и как statement через proc.emit(...).",
    ],
    example: `expr = bitChk(done) == 0
with proc.if_(expr):
    ...`,
    result: "Рендерится как FlowScript condition или statement.",
  },
  {
    id: "domain-speaker-profile-types",
    name: "SpeakerName / CharacterProfile / FlowEnumValue",
    category: "enums",
    section: "enums",
    level: "tool",
    signature: "SpeakerName(...), CharacterProfile(...), FlowEnumValue(...)",
    summary: "Внутренние structured values, на которых построены Speaker, Character и SocialStat.",
    why: "Нужны для advanced расширения библиотеки или добавления новых constants без raw strings.",
    notes: [
      "В обычном коде чаще используют готовые Speaker.NANAKO, Character.YOSUKE, SocialStat.COURAGE.",
    ],
    example: `custom = Character.YOSUKE.with_name("Encoded Name")`,
    result: "Позволяют создавать и переиспользовать typed domain values.",
  },
  {
    id: "bitid-bustup-voicecue",
    name: "BitId / Bustup / VoiceCue",
    category: "enums",
    section: "enums",
    level: "both",
    signature: "BitId(value, name=None), Bustup(character_id, expression_id, ...), VoiceCue(event_major, event_minor, event_sub, cue_id)",
    summary: "Structured IDs для bits, портретов и voice tags.",
    why: "Убирают magic numbers из пользовательского кода и дают читаемый generated FlowScript/MessageScript.",
    notes: [
      "Для bits чаще используй project.reserve_bit(...) или bit(...).",
      "Для портрета персонажа чаще можно передать Character.YOSUKE вместо ручного Bustup(...).",
      "VoiceCue рендерится как [vp ...] перед текстом строки.",
    ],
    example: `msg.line("Partner check.", bustup=Bustup(2, 1), voice=VoiceCue(3, 0, 6, 202))`,
    result: "Рендерит const bits, [bup ...] и [vp ...] там, где это нужно.",
  },
  {
    id: "safety-constants",
    name: "EXPERT / normalize_safety",
    category: "core",
    section: "project",
    level: "standard",
    signature: "EXPERT, normalize_safety(mode, default=STANDARD)",
    summary: "Safety-mode constants и normalization helper.",
    why: "Нужны для tooling и единообразной обработки пользовательских mode values.",
    notes: [
      "Beginner tutorials должны использовать строку 'beginner' или BEGINNER.",
      "EXPERT сейчас относится к advanced/tooling сценарию, а не к первому уроку.",
    ],
    example: `mode = normalize_safety("beginner")`,
    result: "Возвращает нормализованное имя safety mode.",
  },
  {
    id: "doctor-conflict-types",
    name: "DoctorReport / DoctorCheck / ConflictReport / ConflictIssue / ConflictReference",
    category: "diagnostics",
    section: "diagnostics",
    level: "tool",
    signature: "DoctorReport, DoctorCheck, ConflictReport, ConflictIssue, ConflictReference",
    summary: "Structured result objects для doctor и conflict-analysis tools.",
    why: "Нужны, если ты строишь UI или automation поверх диагностики библиотеки.",
    notes: [
      "Обычный пользователь чаще читает already rendered text/log output.",
      "Tooling может использовать эти objects для фильтрации и отображения warnings.",
    ],
    example: `report = run_doctor(project=project)
for check in report.checks:
    print(check.name, check.status)`,
    result: "Даёт programmatic access к diagnostic results.",
  },
  {
    id: "project-data-types",
    name: "ScriptSource / ProjectImport / BitReservation",
    category: "core",
    section: "project",
    level: "tool",
    signature: "ScriptSource(...), ProjectImport(...), BitReservation(...)",
    summary: "Data objects, которые project/build layer использует для source, imports и reserved bits.",
    why: "Нужны в основном для внутренней логики, tests и advanced tooling вокруг build pipeline.",
    notes: [
      "Для пользовательского source обычно вызывай BF(...), Empty(...), FieldBF(...) или EventBF(...), а не ScriptSource напрямую.",
      "ProjectImport появляется после project.import_bf/import_flow/import_msg.",
    ],
    example: `source = BF("original_f007.bf", import_path="original_f007.bf")`,
    result: "Позволяет хранить build metadata структурированно.",
  }
);
const categoryLabels = {
  core: "Project",
  hooks: "Hooks",
  messages: "Messages",
  expressions: "Expressions",
  enums: "Enums",
  diagnostics: "Diagnostics",
};

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function attachCopyButtons(root = document) {
  root.querySelectorAll("pre").forEach((pre) => {
    if (pre.parentElement && !pre.parentElement.classList.contains("code-block")) {
      const wrapper = document.createElement("div");
      wrapper.className = "code-block";
      pre.parentElement.insertBefore(wrapper, pre);
      wrapper.appendChild(pre);
    }

    const container = pre.parentElement;
    if (!container || container.querySelector(".copy-button")) {
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-button";
    button.textContent = "Копировать";
    button.addEventListener("click", async () => {
      const text = pre.innerText;
      try {
        await navigator.clipboard.writeText(text);
        button.textContent = "Скопировано";
        setTimeout(() => {
          button.textContent = "Копировать";
        }, 1600);
      } catch (error) {
        button.textContent = "Ошибка";
        setTimeout(() => {
          button.textContent = "Копировать";
        }, 1600);
      }
    });

    container.appendChild(button);
  });
}

function initSidebarHighlight() {
  const links = Array.from(document.querySelectorAll('.sidebar-nav a[href^="#"]'));
  if (!links.length) {
    return;
  }

  const sections = links
    .map((link) => {
      const id = link.getAttribute("href").slice(1);
      return document.getElementById(id);
    })
    .filter(Boolean);

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

      if (!visible) {
        return;
      }

      const currentId = `#${visible.target.id}`;
      links.forEach((link) => {
        link.classList.toggle("is-active", link.getAttribute("href") === currentId);
      });
    },
    {
      rootMargin: "-25% 0px -55% 0px",
      threshold: [0.1, 0.3, 0.6],
    }
  );

  sections.forEach((section) => observer.observe(section));
}

function renderReferenceDetail(item) {
  const detail = document.getElementById("reference-detail");
  if (!detail) {
    return;
  }

  detail.innerHTML = `
    <div class="detail-header">
      <span class="badge core">${escapeHtml(categoryLabels[item.category] || item.category)}</span>
      <span class="badge ${item.level === "beginner" ? "beginner" : item.level === "standard" ? "standard" : "core"}">${escapeHtml(levelLabels[item.level] || item.level)}</span>
    </div>
    <h2>${escapeHtml(item.name)}</h2>
    <p class="lead">${escapeHtml(item.summary)}</p>
    <div class="signature">${escapeHtml(item.signature)}</div>
    <div class="detail-block">
      <h3>Зачем нужен</h3>
      <p>${escapeHtml(item.why)}</p>
    </div>
    <div class="detail-block">
      <h3>Что важно помнить</h3>
      <ul>${item.notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>
    </div>
    <div class="detail-block">
      <h3>Пример</h3>
      <div class="code-block"><pre><code>${escapeHtml(item.example)}</code></pre></div>
    </div>
    <div class="detail-block">
      <h3>Что получится</h3>
      <p>${escapeHtml(item.result)}</p>
    </div>
  `;

  attachCopyButtons(detail);
}

function initReferenceExplorer() {
  const results = document.getElementById("reference-results");
  const search = document.getElementById("reference-search");
  if (!results || !search) {
    return;
  }

  let activeCategory = "all";
  let activeLevel = "all";
  let activeId = referenceItems[0]?.id || null;

  function filteredItems() {
    const term = search.value.trim().toLowerCase();
    return referenceItems.filter((item) => {
      const matchCategory = activeCategory === "all" || item.category === activeCategory;
      const matchLevel = activeLevel === "all" || item.level === activeLevel;
      const haystack = [
        item.name,
        item.signature,
        item.summary,
        item.why,
        item.category,
        item.section,
        ...item.notes,
      ]
        .join(" ")
        .toLowerCase();
      const matchTerm = !term || haystack.includes(term);
      return matchCategory && matchLevel && matchTerm;
    });
  }

  function renderList() {
    const items = filteredItems();
    if (!items.length) {
      results.innerHTML = `<div class="reference-item"><h3>Ничего не найдено</h3><p>Измени строку поиска или сними часть фильтров.</p></div>`;
      return;
    }

    if (!items.some((item) => item.id === activeId)) {
      activeId = items[0].id;
    }

    results.innerHTML = items
      .map(
        (item) => `
          <button type="button" class="reference-item ${item.id === activeId ? "is-active" : ""}" data-item-id="${escapeHtml(item.id)}">
            <h3>${escapeHtml(item.name)}</h3>
            <p>${escapeHtml(item.summary)}</p>
          </button>
        `
      )
      .join("");

    const selected = referenceItems.find((item) => item.id === activeId);
    if (selected) {
      renderReferenceDetail(selected);
    }

    results.querySelectorAll("[data-item-id]").forEach((button) => {
      button.addEventListener("click", () => {
        activeId = button.getAttribute("data-item-id");
        renderList();
      });
    });
  }

  document.querySelectorAll("[data-filter-type]").forEach((button) => {
    button.addEventListener("click", () => {
      const filterType = button.getAttribute("data-filter-type");
      const filterValue = button.getAttribute("data-filter-value");
      if (filterType === "category") {
        activeCategory = filterValue;
      } else if (filterType === "level") {
        activeLevel = filterValue;
      }

      document
        .querySelectorAll(`[data-filter-type="${filterType}"]`)
        .forEach((chip) => chip.classList.toggle("is-active", chip === button));

      renderList();
    });
  });

  search.addEventListener("input", renderList);
  renderList();
}

document.addEventListener("DOMContentLoaded", () => {
  attachCopyButtons();
  initSidebarHighlight();
  if (document.body.dataset.page === "reference") {
    initReferenceExplorer();
  }
});




