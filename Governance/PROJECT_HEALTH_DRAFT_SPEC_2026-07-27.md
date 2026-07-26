# Project Health — Draft Specification

**Дата:** 2026-07-27  
**Тип документа:** Draft specification (не Candidate, не Accepted контракт)  
**Изменения кода / PIPELINE / DECISION_LOG / HEALTH.md этим файлом не производятся.**

---

## 1. Статус и основание

| Поле | Значение |
|---|---|
| Статус | **Draft** |
| Выбранная основа | **Hypothesis C** (тонкий фактологический слой индикаторов/отчёта + интерпретация в Analyzer) |
| Решение о выборе основы | `DECISION_LOG` **D-2026-07-27-02** |
| Статусный документ модуля | `Governance/HEALTH.md` (Draft, основа C) |
| Workshop | `Governance/HEALTH_DECISION_WORKSHOP_2026-07-27.md` |

**Нормативная опора (проверяемые ссылки):**

| Опора | Содержание для Health |
|---|---|
| Constitution Principle 2 | Нормы и факты разделяются; Health facts ≠ нарратив / норма Gate |
| Constitution Principle 3 | Никто не проверяет сам себя; Analyzer не является единственным источником истины Health |
| Stage / Analyzer | Прецедент: `project_stage.json` (факт) vs `project_analysis.json` (интерпретация) — D-2026-07-26-02; Boundary; Observation #1 |
| Evidence / Accept | Evidence ≠ Accepted; Health ≠ завершение работы — Observation #2; ADR-0002 п.4 |
| D-2026-07-27-02 | Hypothesis C как основа Draft; индикаторы и код не утверждены |
| HEALTH_DECISION_WORKSHOP_2026-07-27.md | Трассируемое Recommendation Workshop (подтверждено человеком в D-02) |

**Факт предварительной проверки репозитория (до проектирования):** отдельных `project_health.json`, `health_status`, Health Engine и зарезервированных Health-индикаторов в коде **нет**. См. §0 ниже (результаты проверки).

### 0. Результаты предварительной проверки следов Health

| След | Где | Вердикт |
|---|---|---|
| `project_health.json` | код / схемы / fixtures | **Не найден** |
| `health_status` | код / схемы | **Не найден** |
| Health Engine (компонент) | `tools/` | **Не найден** (только текст гипотез в Governance) |
| Health-индикаторы (контракт) | код | **Не найдены** |
| `needs_attention` | `tools/project_analyzer.py`, `project_analysis.json`, UI `index.html`, Boundary | Поле **Analyzer**; **не** готовый контракт Project Health (`HEALTH.md` §3) |
| `/api/health` | `tools/local_bridge.py` | Liveness Local Bridge (`ok`, `service`, `orchestrator`); **не** Project Health |
| Упоминания «Project Health» | HEALTH.md, ADR-0002, PIPELINE таблица, Stage Engine FAQ, ORCHESTRATOR, ARCHITECTURE_RISKS, Workshop | Документальные; не runtime-контракт |
| Устаревшие статусы в тексте | `PIPELINE.md` / ADR-0002 всё ещё могут говорить Observation | **Документальный drift** относительно D-02 / HEALTH.md Draft; **не** резерв полей Health |
| Формулировки «по уже спроектированной модели Health» | `ARCHITECTURE_RISKS_AND_DECISIONS.md` | Аспиративно; **не** утверждённый контракт индикаторов |

**Зафиксировано для проектирования:**

- `needs_attention` относится к Analyzer и **не** является готовым контрактом Project Health.  
- `/api/health` является liveness-проверкой Local Bridge и **не** относится к Project Health.  
- Имя будущего артефакта (например `project_health.json`) в этом документе — **Draft-предложение**, не утверждённое решение.

---

## 2. Назначение Project Health

**Задача (Draft):** ответить на вопрос «насколько состояние проекта в порядке?» отдельно от вопроса «на каком этапе проект?» (Stage Engine FAQ / `PROJECT_STAGE_ENGINE.md`).

| Слой | Роль |
|---|---|
| **Health facts** | Проверяемые факты/индикаторы состояния (thin layer); детерминированный отчёт |
| **Health interpretation** | Объяснение этих фактов человеку через Analyzer; зоны внимания, мягкий нарратив |

**Не смешивать:**

| Не является | Почему (опора) |
|---|---|
| Stage | Stage Engine — единственный источник `stage` (D-02; ADR-0002) |
| Accept / Delivery complete | Observation #2; Evidence ≠ Accepted |
| Action Gate | PIPELINE / CHANGE_PROTOCOL; HEALTH.md: не заменяет Gate |

---

## 3. Архитектурная модель Hypothesis C

Опора: `HEALTH.md` §2; D-2026-07-27-02; прецедент Stage/Analyzer.

### 3.1. Thin Health Layer

Детерминированный тонкий слой индикаторов.

Он:

- собирает или вычисляет **проверяемые** факты из уже существующих артефактов проекта (в первую очередь `.ai-pos/project_stage.json` и fs-маркеры, уже используемые Engine/Analyzer);
- **не** создаёт нарратив;
- **не** назначает Stage;
- **не** принимает решения Accept / archive;
- **не** заменяет Review;
- **не** объявляет работу Accepted;
- **не** является полным «умным» Health Engine класса Hypothesis A (D-02: полный код Health не утверждён).

### 3.2. Analyzer Interpretation

Analyzer:

- **читает** Health facts (когда артефакт появится; сейчас читает stage и пишет analysis);
- объясняет их человеку;
- может указывать зоны внимания (в т.ч. существующее поле `needs_attention` остаётся интерпретацией, не фактом Health);
- **не** изменяет исходные Health facts;
- **не** становится источником истины Health (Constitution П.3; Hypothesis C).

---

## 4. Границы ответственности

| Область | Отвечает | Не отвечает |
|---|---|---|
| **Stage Engine** | `stage`, `confidence_state`, evidence стадии, blockers стадии, `project_stage.json` | Оценка «здоровья»; Accept; нарратив Health |
| **Thin Health Layer** | Детерминированные Health indicators / facts-отчёт | Stage; Gate; UI-копирайт; мягкие рекомендации |
| **Analyzer** | Интерпретация stage и (Draft) Health facts; `project_analysis.json` | Истина Stage; истина Health facts; Action Gate |
| **Evidence (адаптеры / fs)** | Поставка system-confirmed / user-confirmed сигналов | Accept; назначение stage; итоговый Health narrative |
| **Action Gate** | Подтверждение человеком значимых изменений норм/контура | Вычисление индикаторов; stage |
| **Orchestrator** | Порядок запуска компонентов; режимы NORMAL/DIAGNOSTIC/BLOCKED | Источник истины о стадии или здоровье (`ORCHESTRATOR.md` §1) |
| **UI** | Отображение уже вычисленных артефактов понятным языком | Назначение stage/health; подмена Gate |

---

## 5. Кандидаты Health-индикаторов

**Важно:** это **не** окончательное утверждение схемы. Статус каждого пункта — **Draft candidate**.  
Опора только на существующие артефакты: `project_stage.json` (в т.ч. `presence`, `blockers`, `conflicting_evidence`, `source_freshness`), marker-файлы проекта, контракт Analyzer MVP (как **источник данных для интерпретации**, не как Health fact).

`needs_attention` **не** используется как готовый индикатор Health.

### 5.1. Подтверждённые текущей архитектурой (есть данные в MVP-артефактах)

#### H-IND-01 — `stub_documents_present`

| Поле | Содержание |
|---|---|
| Назначение | Зафиксировать наличие файлов-заглушек, уже учитываемых Engine |
| Источник данных | `project_stage.json` → `presence.stub_files` (и/или evidence с кодами `*_STUB`) |
| Детерминированность | Высокая (при валидном stage artifact) |
| Способ вычисления | `len(presence.stub_files) > 0` или непустой список stub evidence codes |
| Допустимые значения | `false` \| `true`; опционально `count: number`, `files: string[]` |
| Не означает | Что stage неверен; что работа Accepted; что проект «плох» морально |
| Риск ложной интерпретации | Путать «есть заглушки» с «нужно немедленно остановить работу» |

#### H-IND-02 — `stage_blockers_present`

| Поле | Содержание |
|---|---|
| Назначение | Наличие blockers, уже вычисленных Stage Engine |
| Источник данных | `project_stage.json` → `blockers` |
| Детерминированность | Высокая |
| Способ вычисления | `len(blockers) > 0`; опционально `count = len(blockers)` |
| Допустимые значения | `false` \| `true`; опционально `count: number`; **references** вида `{ "path": ".ai-pos/project_stage.json", "field": "blockers" }` (указатель на источник, не копия содержимого) |
| Не означает | Новый набор blockers от Health; смену stage; право Health владеть формулировками blockers |
| Риск ложной интерпретации | Дублировать UI stage blockers как «отдельный вердикт Health» без ссылки на stage |
| Запрет копирования NL | Health **не** копирует естественно-языковой текст Stage (`blockers[].text` и аналоги). Для чтения формулировок потребитель обращается к Stage artifact по `references`. |

**Правило Draft (Thin Health Layer):** Health facts не включают копирование естественно-языкового текста Stage Engine (blockers text, evidence text, next_step text и т.п.); допускаются boolean/count и structural references `{path, field}`.

#### H-IND-03 — `conflicting_stage_evidence_present`

| Поле | Содержание |
|---|---|
| Назначение | Сигнал конфликтующих evidence стадии |
| Источник данных | `project_stage.json` → `conflicting_evidence` |
| Детерминированность | Высокая |
| Способ вычисления | `len(conflicting_evidence) > 0` |
| Допустимые значения | `false` \| `true` |
| Не означает | Автоматический PROVISIONAL (это поле Engine); Accept |
| Риск ложной интерпретации | Считать конфликт доказательством «красного здоровья» без чтения состава evidence |

#### H-IND-04 — `stage_snapshot_stale_flag`

| Поле | Содержание |
|---|---|
| Назначение | Флаг устаревания снимка стадии, уже предусмотренный контрактом Engine |
| Источник данных | `project_stage.json` → `source_freshness.stale` |
| Детерминированность | Высокая (как записано Engine) |
| Способ вычисления | Копирование boolean `source_freshness.stale` |
| Допустимые значения | `false` \| `true` |
| Не означает | Что Orchestrator обязан был обновить stage; что analysis устарел (отдельный артефакт) |
| Риск ложной интерпретации | Приравнять stale stage к «проект заброшен» |

#### H-IND-05 — `substantive_context_absent`

| Поле | Содержание |
|---|---|
| Назначение | Отсутствие содержательного context-маркера при наличии/отсутствии файлов по правилам Engine |
| Источник данных | `presence.context_hits` пуст **и** context stubs/отсутствие файлов по правилам substantive Engine (`substantive_rules` в stage / marker set Boundary) |
| Детерминированность | Высокая при опоре на уже посчитанный `presence` Engine |
| Способ вычисления | `context_hits == []` (факт presence); не пересчитывать stage |
| Допустимые значения | `false` \| `true` |
| Не означает | Обязательность ROADMAP; запрет работы пользователя |
| Риск ложной интерпретации | Смешать с `needs_attention` Analyzer (похожий текст, другой слой) |

### 5.2. Требующие дополнительного исследования

| ID | Кандидат (Draft idea) | Почему открыт | Какие Evidence нужны |
|---|---|---|---|
| H-IND-R01 | Агрегированный `health_level` (ok / attention / critical) | В коде и Accepted-контрактах **нет** шкалы; ARCHITECTURE_RISKS апеллирует к будущей модели | Пилот на TEMPLATE + mini_filled; правило агрегации без подмены stage |
| H-IND-R02 | Review overdue / post-review signals | Упоминается в ARCHITECTURE_RISKS; модуля Review workflow в Accepted runtime **нет** | Появление артефакта review state; иначе не включать в thin layer |
| H-IND-R03 | GitHub inactivity / release signals | ADR: внешнее = evidence, не Accept; адаптеры MVP не активированы (`OPTIONAL_ADAPTER_*` reserved) | Активный adapter + политика trust |
| H-IND-R04 | Расхождение stage `next_step` vs фактические маркеры | Может дублировать Engine; нужен proof of independent value | Контрпримеры, где Health факт ≠ stage blocker |
| H-IND-R05 | Свежесть `project_analysis.json` vs Health facts | TTL/порядок Orchestrator; Health артефакта ещё нет | После появления Health artifact: правила DIAGNOSTIC при рассинхроне |

---

## 6. Предварительный контракт данных

**Draft-предложение имени файла:** `.ai-pos/project_health.json`  
**Имя не утверждено** без отдельного решения (D-02: контракт индикаторов не утверждён).

**Фактологический артефакт не содержит:** `narrative`, `recommendation`, `stage` (как назначаемое поле), копий `stage_explanation`.

### 6.1. Корневые поля (Draft)

| Поле | Тип | Обязательность | Источник | Семантика |
|---|---|---|---|---|
| `schema_version` | string | обязательное | Thin Health Layer | Версия схемы фактов, напр. Draft-предложение `ai-pos.project_health/v0` |
| `generated_at` | string (ISO-8601 UTC) | обязательное | Thin Health Layer | Время расчёта отчёта |
| `project_path` | string | обязательное (MVP-путь) | Корень проекта | Абсолютный/нормализованный путь; `project_id` — **открытый вопрос**, если появится стабильный id |
| `calculation_status` | enum string | обязательное | Thin Health Layer | `ok` \| `failed` \| `partial` — удалось ли посчитать facts |
| `indicators` | object \| array | обязательное при `ok`/`partial` | Thin Health Layer | Набор H-IND-* значений без нарратива |
| `source_artifacts` | array of objects | обязательное | Thin Health Layer | Ссылки на входы, напр. `{ "path": ".ai-pos/project_stage.json", "role": "stage_facts" }` |
| `warnings` | array of strings | обязательное (может быть `[]`) | Thin Health Layer | Машинные предупреждения расчёта (нет stage file, partial), **не** user-facing essay |

### 6.2. Элемент индикатора (Draft shape)

| Поле | Тип | Обязательность | Семантика |
|---|---|---|---|
| `id` | string | обязательное | Напр. `stub_documents_present` |
| `value` | boolean \| number \| string \| object | обязательное | Детерминированное значение |
| `based_on` | string[] | рекомендуемое | Ключи/`path` источников |

---

## 7. Связь с `project_analysis.json`

| Тема | Правило (Draft) | Опора |
|---|---|---|
| Что Analyzer может читать из Health | При наличии Health artifact — `indicators`, `calculation_status`, `warnings`, `source_artifacts` | Hypothesis C; Boundary роль Analyzer |
| Что только в analysis | `stage_explanation`, `needs_attention`, мягкий `next_step` текст, любые recommendations/narrative | Boundary §2.1; MVP schema analysis |
| Почему `needs_attention` остаётся интерпретацией | Строится эвристиками Analyzer из stage/fs; не имеет отдельного Health schema; HEALTH.md запрещает выдавать его за контракт Health | `project_analyzer.py` `build_needs_attention`; HEALTH.md §3 |
| Как избежать двух картин | UI/потребители: Stage truth только из `project_stage.json`; Health facts только из Health artifact; analysis — подпись «объяснение». Запрет Analyzer переписывать Health facts и stage | Observation #1; D-02; П.2 |

**Факт сегодня:** Analyzer копирует `stage` / `confidence_state` из stage file и пишет `needs_attention` — это **не** нарушает будущий контракт, пока Health facts отсутствуют; после появления Health artifact analysis может **цитировать** indicators, не дублируя их как вторую истину.

---

## 8. Терминологические и технические коллизии

| Утверждение | Статус |
|---|---|
| Project Health ≠ `/api/health` | **Факт** (`local_bridge.py`) |
| Project Health ≠ liveness | **Факт** |
| Project Health ≠ `needs_attention` | **Факт** + норма HEALTH.md §3 |
| Project Health ≠ Stage | **Норма** Stage Engine / D-02 / HEALTH.md |
| Project Health ≠ Accepted | **Норма** Observation #2 / PIPELINE |
| Project Health ≠ Action Gate | **Норма** PIPELINE / CHANGE_PROTOCOL / HEALTH.md |

---

## 9. Non-goals

Этот Draft **не**:

- проектирует UI;
- разрешает или содержит код реализации;
- меняет `PIPELINE.md`;
- создаёт полный Health Engine (Hypothesis A);
- утверждает окончательный набор индикаторов;
- вводит автоматическую блокировку действий по Health;
- переводит модуль в Candidate или Accepted;
- изменяет `DECISION_LOG` / `HEALTH.md` сам по себе.

---

## 10. Открытые вопросы

### Q1 — Имя и размещение артефакта

- **Вопрос:** Фиксировать ли `.ai-pos/project_health.json` и schema id?  
- **Почему открыт:** D-02 не утверждал имя файла.  
- **Evidence:** согласованность с `project_stage.json` / `project_analysis.json`; отсутствие коллизии с `/api/health`.  
- **Позднее решение:** явное Accepted/Candidate решение по имени схемы.

### Q2 — Минимальный обязательный набор H-IND-*

- **Вопрос:** Какие из H-IND-01…05 обязательны в v0?  
- **Почему открыт:** пилотных Evidence на двух фикстурах недостаточно для закрытия Candidate.  
- **Evidence:** прогон TEMPLATE (stubs) и mini_filled (substantive) → ожидаемые values.  
- **Позднее решение:** freeze списка индикаторов v0.

### Q3 — Нужен ли агрегатный `health_level`

- **Вопрос:** Вводить ли ok/attention/critical?  
- **Почему открыт:** отсутствует в MVP; риск подмены Gate/паники UI (Stage Engine UX note).  
- **Evidence:** пользовательские сценарии; сравнение с одними только boolean indicators.  
- **Позднее решение:** принять или явно отвергнуть агрегат в Candidate.

### Q4 — Место Thin Health Layer в Orchestrator

- **Вопрос:** Порядок: Engine → Health → Analyzer или Engine → Analyzer с отложенным Health?  
- **Почему открыт:** ORCHESTRATOR Accepted описывает Engine→Analyzer; Health шаг не канонизирован.  
- **Evidence:** влияние на режимы NORMAL/DIAGNOSTIC/BLOCKED; stale analysis rules.  
- **Позднее решение:** изменение Orchestrator только через pipeline (значимое по CHANGE_PROTOCOL).

### Q5 — `project_id` vs только `project_path`

- **Вопрос:** Нужен ли стабильный id?  
- **Почему открыт:** MVP Analyzer/Engine используют path.  
- **Evidence:** мультикорень / перенос папок.  
- **Позднее решение:** схема id или отказ.

### Q6 — Синхронизация устаревших упоминаний Observation в PIPELINE/ADR

- **Вопрос:** Обновлять ли таблицы статуса Health в PIPELINE/ADR текстом Draft?  
- **Почему открыт:** документальный drift после D-02; вне scope этой спеки.  
- **Evidence:** сверка ссылок Governance.  
- **Позднее решение:** отдельный doc-sync (не код Health).

---

## 11. Evidence Checklist для Draft → Candidate

| # | Проверяемое утверждение | Артефакт / тест | Критерий прохождения | Возможный источник ошибки |
|---|---|---|---|---|
| E1 | Thin layer не записывает `stage` | Контракт + тест фикстуры | В Health artifact нет назначаемого `stage` | Случайная копия поля stage в schema |
| E2 | Indicators детерминированы на TEMPLATE | Вычисление на `Projects/TEMPLATE` | Стабильные values при повторном прогоне без изменения файлов | Зависимость от clock кроме `generated_at` |
| E3 | Indicators детерминированы на mini_filled | То же для `Projects/FIXTURES/mini_filled` | Отличие от TEMPLATE объяснимо presence/blockers stage | Подмешивание analysis narrative |
| E4 | Analyzer не мутирует Health facts | Тест/инспекция записи | После analysis Health file byte-stable (кроме параллельного пересчёта Health) | Analyzer пишет в тот же файл |
| E5 | `needs_attention` ≠ Health indicator id | Спека + код review | Нет indicator id `needs_attention` | «Удобный» алиас в реализации |
| E6 | `/api/health` не читает Project Health | Bridge review (`tools/local_bridge.py`) | Ответ liveness без indicators / без чтения Health artifacts | Переиспользование пути `/api/health` |
| E7 | UI не показывает Health facts как Stage | UI review (когда появится отображение) | Подписи/источники разделены | Один блок «статус» смешивает поля |
| E8 | Нет автоматической блокировки Gate | Спека + отсутствие lock API | Health не закрывает Action Gate | «Критичный» агрегат блокирует UI |
| E9 | Документы Governance согласованы со статусом Draft | Сверка HEALTH.md, D-02, эта спека, PIPELINE.md | Статус Health в канонических таблицах = Draft (после D-02) | Старый текст Observation как «текущий закон» без D-02 |

### 11.1. Draft Review — статус Evidence (2026-07-27)

| # | Статус Review | Фиксация |
|---|---|---|
| E1 | **Contract passed** | Контракт Draft запрещает назначаемое поле `stage` в фактологическом Health artifact (§6); копирование NL Stage запрещено (§5 H-IND-02). Executable тест реализации — вне scope (кода нет). |
| E2 | **manual expected values established; executable verification pending implementation** | Ожидаемая логика на TEMPLATE выводима из текущего `project_stage.json` (stubs/blockers); исполняемой верификации Thin Health Layer нет. |
| E3 | **manual expected values established; executable verification pending implementation** | То же для `Projects/FIXTURES/mini_filled` (substantive context; отличие от TEMPLATE объяснимо stage presence/blockers). |
| E4 | Pending implementation | Health artifact в runtime отсутствует; проверка мутации Analyzer невозможна до появления файла. |
| E5 | **Contract passed** | В кандидатах H-IND-* нет id `needs_attention`; `needs_attention` явно исключён как Health indicator (§5, §8). |
| E6 | **Verified against current Bridge code** | См. §11.2. |
| E7 | **Not applicable until UI exists** | UI Project Health facts не реализован; смешение с Stage в интерфейсе проверить нельзя. |
| E8 | **partial current-state verification only** | Спека запрещает блокировку Gate (§9); в текущем коде нет Health→Gate lock API. Полная проверка «агрегат не блокирует» — после появления агрегата/UI. |
| E9 | **Failed** | `Governance/PIPELINE.md` в таблице текущего контура всё ещё указывает Project Health как **Observation** (+ Hypothesis A/B/C), тогда как D-2026-07-27-02 и `HEALTH.md` фиксируют **Draft** (основа C). **PIPELINE.md этим Review не исправляется** (отдельное решение / doc-sync). |

### 11.2. E6 — проверка `tools/local_bridge.py` (факт, код не менялся)

В `BridgeHandler.do_GET` путь `/api/health` возвращает только JSON:

- `ok: true`
- `service: "ai-pos-local-bridge"`
- `orchestrator: <имя файла orchestrator>`

Обработчик **не** открывает и **не** читает `project_health.json`, indicators или иные Project Health artifacts. Чтение проектных insight-артефактов в Bridge связано с другим endpoint (`POST /api/refresh-insight`), не с `/api/health`.

**Вывод E6:** при текущем коде `/api/health` не читает Project Health artifacts (liveness only).

---

## 12. Следующий разрешённый шаг

**Единственный следующий шаг после подготовки этого документа:**  
Review человеком `Governance/PROJECT_HEALTH_DRAFT_SPEC_2026-07-27.md` (и при необходимости уточнение Draft-текста).

**Не разрешается автоматически:** реализация Thin Health Layer, изменение Orchestrator, правка PIPELINE, переход в Candidate, коммит «за реализацию».

Любая реализация или Candidate — только после **явного** решения человека по итогам Review.

---

Project Health Draft Specification подготовлена.

Окончательный контракт индикаторов не утверждён.

Реализация не разрешена.

Переход в Candidate не выполнен.

Ожидается Review и явное решение человека.
