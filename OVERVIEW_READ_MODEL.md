# AI POS — Overview Read Model

**Статус:** архитектурный контракт (Этап 0 моста Stage Engine → Overview)  
**Дата:** 2026-07-27  
**Область:** только проекция данных на экран «Обзор»; без назначения стадии, без Health, без планировщика задач  
**Связанные документы:** `PROJECT_STAGE_ENGINE.md`, `PROJECT_ANALYZER_AND_STAGE_BOUNDARY.md`, `Governance/ORCHESTRATOR.md`, `Governance/DECISION_LOG.md` (D-2026-07-26-04)  
**Контрольный проект:** `D:\Cursor Проект Мой день` (baseline Этапа −1)

**Вне области этого документа:** изменение Stage Engine / Analyzer; запись System в карточку проекта; реализация UI (следующие этапы плана моста).

---

## 1. Назначение

Overview Read Model — **тонкая read-only проекция** трёх независимых слоёв данных на поля вкладки «Обзор».

Он отвечает на вопрос:

> Откуда каждое поле Обзора берёт значение, что показывать при сбое System, и что System **не имеет права** перезаписывать?

Он **не**:

- не назначает Project Stage (это Stage Engine);
- не заменяет Analyzer-сводку;
- не является Workflow State и не хранит модуль/задачу;
- не подменяет решение человека в Review.

Потребитель модели — UI Обзора. Источник истины для стадии по-прежнему `project_stage.json` (см. `PROJECT_ANALYZER_AND_STAGE_BOUNDARY.md`).

---

## 2. Три слоя источников

| Слой | Вопрос | Типичное хранение (факт MVP) | Кто пишет |
|------|--------|------------------------------|-----------|
| **Passport** | Что это за проект и где он лежит? | Карточка проекта: `name`, `idea`, `workFolder`, URL-поля, `status` (рабочий) | Человек / форма паспорта |
| **Workflow** | Какой модуль и задача активны сейчас? | `modules[]`, `activeModuleId`, `tasks[]`, `activeTaskId`, поля задачи, Review | Человек / UI workflow |
| **System** | На каком этапе жизненного цикла проект по фактам диска? | `.ai-pos/project_stage.json` → `project_analysis.json` → Local Bridge API → `cliAnalysisCache` | Stage Engine + Analyzer + Orchestrator |

Слои **не сливаются** в один объект истины. Обзор **читает** все три и **маркирует** происхождение.

Термины Stage ≠ Workflow ≠ Status из `PROJECT_STAGE_ENGINE.md` здесь конкретизируются для UI (см. §8).

---

## 3. Владелец каждого поля экрана «Обзор»

| Поле UI | Слой-владелец | Главный источник | Резервный источник | Заметки |
|---------|---------------|------------------|--------------------|---------|
| Проект | Passport | `project.name` | — | Не из System |
| Модуль | Workflow | активный модуль | — | System имени модуля не знает (MVP) |
| **Этап проекта** | **System** | `cliAnalysisCache` ok → `stage` (+ label); истина на диске — `project_stage.json` | последний ok-cache / «не определён» | **Не** `project.stage` карточки |
| Необходимо сделать (название задачи) | Workflow | `task.name` | — | |
| Необходимо сделать (пункты) | Workflow | `subtask` / `goal` / `module.remaining` | мягкая цитата System `next_step` как подсказка, не замена списка | |
| Ожидаемый результат | Workflow | `task.expectedResult` | критерии Review | |
| Следующее действие (система) | System | `analysis.next_step` / stage `next_step` | текст «системный шаг недоступен» | |
| Следующее действие (инструмент) | Workflow / Passport tool choice | `recommendedTool` / выбранный AI tool | последний выбранный tool | Не путать с системным next_step |
| Проверка / URL | Passport | `projectUrl` / `previewUrl` / `localUrl` / … | инструкция открыть вручную | `workFolder` ≠ URL |
| Решение после проверки | Workflow Review | `task.review` (+ localStorage reviews) | тот же Review на вкладке задачи | Только человек |
| Блокировки / внимание (системные) | System | `needs_attention`, при наличии — stage `blockers`; mode BLOCKED/DIAGNOSTIC | баннер «система недоступна» | Не смешивать с Review |
| Дата последнего анализа | System | `detected_at` / `fetchedAt` в cache | «дата неизвестна» | Пока UI может не показывать — контракт требует поле в модели |

Поле карточки `project.stage` (пример: «Разработка») — **не** Project Stage. По D-2026-07-26-04 это локальное рабочее состояние карточки; на Обзоре его **нельзя** выдавать за системный этап. До вывода из UI — только как опциональная «рабочая метка» с явной маркировкой Passport/Workflow, отдельным блоком.

---

## 4. Запрет записи System → Passport / Workflow

Запрещено при Refresh / apply analysis / открытии проекта:

1. Записывать `analysis.stage` / `project_stage.stage` в `project.stage`, `project.currentStage`, имя модуля или задачи.
2. Создавать / переключать `activeModuleId` / `activeTaskId` по `action_hint`.
3. Менять `task.review` / notes / accepted по результату Analyzer.
4. Подменять `expectedResult`, `canChange`, материалы паспорта.

Разрешено:

- обновлять только **System-проекцию** (cache / read-model);
- показывать System рядом с Passport/Workflow;
- предлагать человеку действия («обновить анализ», «добавить задачу») без автозаписи.

Это согласуется с Orchestrator: координатор не подменяет Review и не является истиной о Workflow.

---

## 5. Поведение при состояниях System

Состояния берутся из `cliAnalysisCache.kind` и/или `analysis.valid` / Orchestrator `mode` (как в Local Bridge).

| Состояние | Условие (ориентир) | Этап проекта на Обзоре | Системный next_step | Системные блокировки |
|-----------|--------------------|------------------------|---------------------|----------------------|
| **ok** | cache ok, `valid !== false`, есть `stage` | Показать label/code из System | Показать `next_step` | Показать `needs_attention` / blockers, если не пусты |
| **stale** | был ok, но данные старше порога свежести *или* файлы на диске новее cache (когда появится сверка) | Показать последнее значение + метка «устарело» | То же + «устарело» | Не скрывать; пометить устаревшими |
| **invalid** | `valid: false` / kind invalid | «Системный этап недействителен» — **не** подставлять `project.stage` | Не показывать как актуальный шаг | Показать ошибку анализа |
| **blocked** | Orchestrator `BLOCKED` | «Анализ заблокирован» | Не выдавать за рабочий шаг | Показать reason / message |
| **unavailable** | нет Bridge / нет `workFolder` / нет cache / file:// | «Системный этап не загружен» | «Недоступно» | Баннер: как запустить Bridge / указать папку |

**Жёсткое правило:** при invalid / blocked / unavailable **запрещено** маскировать дыру текстом Passport `project.stage` («Разработка»), чтобы не создать ложную «системную» картину.

Passport и Workflow при любом состоянии System **продолжают отображаться** как есть.

---

## 6. Маркировка источника и свежести в UI

Минимальный контракт отображения (реализация — на этапах 1–2 плана моста):

1. **Чип источника** у системных полей: `Система` | `Вручную` | `Недоступно`.
2. **Свежесть** у System: `только что` / `N мин назад` / `устарело` / `дата неизвестна` — от `detected_at` (stage) и/или `fetchedAt` (момент ответа API).
3. **Confidence** только у Project Stage (System): CONFIRMED / PROVISIONAL / UNKNOWN — простым языком.
4. Passport/Workflow-поля: чип `Вручную` (или без чипа, если визуально ясно, что это постановка человека).
5. Две строки next_step не сливать в одну без разделителя слоёв.

---

## 7. Baseline контрольного проекта «Мой день»

Путь: `D:\Cursor Проект Мой день`  
Карточка UI (DEMO): `demo-moy-den`, `workFolder` = этот путь.

| Слой | Факт baseline (Этап −1) |
|------|-------------------------|
| System | После Refresh: `EXECUTION` / «Выполнение», `CONFIRMED`, `detected_at` обновлён; next_step — продолжить задачу модуля и проверить результат |
| Passport / карточка | `project.stage` = «Разработка»; `status` = «В работе» |
| Workflow | Модуль «Историческая справка»; задача про раскрытие карточки |
| Обзор сегодня | Показывает «Разработка» как «Текущий этап» из карточки; System только в блоке «Анализ проекта» |

### Почему System = EXECUTION, а Обзор = «Разработка»

Это **не** противоречие Stage Engine и не ошибка Analyzer. Это **два разных поля из двух слоёв**, которые UI сейчас смешивает под одной подписью:

1. **System** вычислил жизненный цикл по файлам диска (контекст, roadmap, architecture, runtime `index.html` + `js/`/`css/`) → `EXECUTION`.
2. **Passport/карточка** хранит ручную (демо) метку `project.stage = "Разработка"` — локальное состояние UI, **не** результат Engine (D-2026-07-26-04).
3. `renderOverview` читает карточку; `renderCliInsight` читает cache. Мост Read Model отсутствует → на одном экране два ответа на вопрос «какой этап?».

Контракт Этапа 0: на Обзоре «Этап проекта» = только System; «Разработка» не является Project Stage.

---

## 8. Терминология (обязательная для UI и документов моста)

| Термин | Значение | Не путать с |
|--------|----------|-------------|
| **Project Stage** | Жизненный цикл: `IDEA…EXECUTION` (и целевые стадии Engine) | `project.stage` карточки, «Разработка» |
| **Рабочий статус** | Метка Passport/Workflow: «В работе», «Пауза» (`project.status` / status модуля) | `analysis.status` (`ok` / `invalid`) |
| **Состояние анализа** | Технический результат прогона: ok / invalid / blocked / … | Рабочий статус проекта |
| **Workflow Review** | Решение человека по задаче: unchecked / notes / accepted | GitHub PR review; анализ Analyzer |
| **Системное next_step** | Логический шаг от стадии (`project_stage` / analysis) | «Выполнить в Cursor» |
| **Инструмент выполнения** | Где копировать/делать задание (Cursor и др.) | Системное next_step |
| **Passport** | Паспорт проекта (имя, папка, URL, рабочий статус) | System insight |
| **Workflow** | Модуль, задача, шаг задачи, Review | Project Stage |
| **System** | Stage + analysis + cache после Bridge | Ручная постановка |

---

## 9. Путь данных System (справка)

```text
Local Bridge POST /api/refresh-insight
  → Orchestrator (Stage Engine → Analyzer)
  → .ai-pos/project_stage.json
  → .ai-pos/project_analysis.json
  → API { ok, analysis, mode, … }
  → cliAnalysisCache[projectId]
  → (цель) Overview Read Model → поля Обзора с чипом «Система»
  → (факт сегодня) только renderCliInsight
```

---

## 10. Критерий готовности следующих этапов

Этап моста считается согласованным с этим контрактом, если на контрольном проекте «Мой день»:

- после Refresh Обзор показывает Project Stage **Выполнение / EXECUTION**, а не «Разработка» как системный этап;
- модуль и задача DEMO остаются Workflow и не затираются;
- при недоступном Bridge Обзор не подставляет «Разработку» вместо System.

---

## 11. История

| Дата | Событие |
|------|---------|
| 2026-07-27 | Этап 0: документ создан по baseline Этапа −1 |
