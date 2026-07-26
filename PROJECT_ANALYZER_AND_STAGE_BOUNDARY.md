# AI POS — Граница: Project Stage Engine и project_analyzer

**Статус:** архитектурное описание; MVP реализован, полная модель — целевая архитектура  
**Дата:** 2026-07-26  
**Связанные документы:** `PROJECT_STAGE_ENGINE.md`, `Governance/ORCHESTRATOR.md`, `Governance/HEALTH.md` (Observation)  

**Реализация (факт):**  
- Stage Engine MVP: `tools/project_stage_engine.py`  
- Analyzer MVP: `tools/project_analyzer.py`  
- Orchestrator MVP: `tools/refresh_project_insight.py` (порядок Engine → Analyzer)  
- Полная модель fact sources / GitHub / Stage History / расширенный контракт analysis в этом документе остаётся **целевой**; ниже §5 описывает **фактический** MVP-контракт `project_analysis.json`  

**Важно о коде:** `tools/project_analyzer.py` **не удалять** — компонент контура развития. Analyzer не назначает и не переписывает стадию.

---

## 1. Зачем разделение

Два разных вопроса нельзя смешивать в одном выводе:

| Вопрос | Отвечает | Характер |
|---|---|---|
| На каком этапе проект и что из этого следует логически? | **Project Stage Engine** | Детерминированный, на evidence |
| Что ещё важно знать: риски, сводка, мягкие рекомендации? | **project_analyzer** | Аналитический, вероятностный / эвристический |

Если analyzer сам «выбирает стадию», появляется вторая истина, ИИ может подтянуть удобный этап, а UI и Health начинают спорить друг с другом.

---

## 2. Роли компонентов

### 2.1. `project_analyzer.py` (контур развития)

**Делает (MVP, факт кода):**
- читает `.ai-pos/project_stage.json` (без него — invalid analysis, `stage: null`);
- копирует `stage` и `confidence_state` из stage file;
- пишет `.ai-pos/project_analysis.json`: `stage_explanation`, `what_is_present`, `needs_attention`, `next_step`;
- объясняет уже известную стадию простым языком.

**Целевая роль (полная модель, не всё реализовано в MVP):**
- расширенная сводка, риски, мягкий фокус внимания поверх фактов проекта.

**Не делает:**
- не блокирует действия (не Action Gate, не Review lock);
- не является источником истины для стадии;
- не записывает и не переопределяет `project_stage.json`;
- не назначает `CONFIRMED` стадию (и вообще не выбирает `stage` самостоятельно).

### 2.2. Project Stage Engine (отдельный компонент)

**Делает:**
- работает строго по `PROJECT_STAGE_ENGINE.md`;
- собирает подтверждённые evidence (system-confirmed / user-confirmed; AI-inferred только как слабый сигнал);
- возвращает: `stage`, `confidence_state`, `blockers`, `evidence`, `next_step` (логический, от стадии);
- пишет результат в `project_stage.json` (+ Stage History по правилам Engine).

**Не делает:**
- не подменяет Project Health;
- не заменяет analyzer-сводку;
- не позволяет исполняющему ИИ единолично выставить `confidence_state = CONFIRMED`.

---

## 3. Разделение артефактов результата

| Файл | Содержание | Источник истины? |
|---|---|---|
| **`project_stage.json`** | Фактическая (вычисленная Engine) стадия, confidence, evidence, blockers, next_step от стадии | **Да — для стадии** |
| **`project_analysis.json`** | Вероятностная / эвристическая сводка, риски, наблюдения, мягкие рекомендации analyzer | **Нет для стадии**; аналитический слой |

Рекомендуемое размещение (если проект уже использует `.ai-pos/`):

```text
.ai-pos/
  project_stage.json       ← Stage Engine
  project_analysis.json    ← project_analyzer
  project_state.json       ← workflow / user state (как ранее)
```

Analyzer **читает** `project_stage.json` и может цитировать его поля в сводке.  
Analyzer **не пишет** стадию обратно в `project_stage.json`.

---

## 4. Минимальная схема взаимодействия

```text
Fact sources (Intake, Discovery, Artifacts, Workflow,
Review, Delivery, optional GitHub evidence)
        │
        ▼
Project Stage Engine  (детерминированный)
        │
        │  пишет / обновляет
        ▼
project_stage.json
  (stage, confidence_state, evidence, blockers, next_step)
        │
        │  только чтение стадии
        ├────────────────────────────┐
        ▼                            ▼
project_analyzer.py              UI / Health / Gate
  читает stage.json              используют stage
  + другие факты                 как факт этапа
  пишет analysis.json
        │
        ▼
project_analysis.json
  (MVP: stage, confidence_state, stage_explanation,
   what_is_present, needs_attention, next_step; см. §5)
```

### Порядок вызова (минимальный контракт)

1. **Сначала** Stage Engine (или берётся свежий `project_stage.json`, если TTL не истёк).  
2. **Затем** `project_analyzer.py`:  
   - вход: путь проекта, `project_stage.json`;  
   - выход: `project_analysis.json`.  
3. Клиенты читают:  
   - стадию — из `project_stage.json` (истина);  
   - объяснение и сводку MVP — из `project_analysis.json`;  
   - analyzer повторяет `stage` / `confidence_state` **копированием** из stage file, не как собственный выбор.

### Если стадии ещё нет

```text
project_stage.json отсутствует или невалиден
  → Analyzer не выдумывает stage
  → пишет project_analysis.json с valid=false, stage=null
  → (invalidate_analysis) ошибка в поле error
```

Запрещено: `inferred_stage` в analysis как замена Engine.

---

## 5. Что лежит в каждом JSON

### `project_stage.json` (факт MVP Engine)

Пишет `tools/project_stage_engine.py` (`engine`: `project_stage_engine_mvp_min`).

```json
{
  "schema": "ai-pos.project_stage/v1",
  "stage": "PLANNING",
  "stage_label": "Планирование",
  "confidence_state": "CONFIRMED",
  "evidence": [],
  "conflicting_evidence": [],
  "blockers": [],
  "next_step": { "text": "…", "action_hint": "…" },
  "detected_at": "2026-07-26T00:00:00Z",
  "engine": "project_stage_engine_mvp_min",
  "mvp_note": "Temporary minimal Stage Engine (IDEA..EXECUTION)."
}
```

MVP-стадии Engine: `IDEA | INTAKE | DISCOVERY | PLANNING | EXECUTION`.  
Полный набор стадий из `PROJECT_STAGE_ENGINE.md` — целевая модель.

### `project_analysis.json` (факт MVP Analyzer)

Пишет `tools/project_analyzer.py` (`analyzer`: `project_analyzer_mvp_min`).  
Поля `stage` и `confidence_state` **копируются** из `project_stage.json`.

Успешный прогон (`valid: true`):

```json
{
  "schema": "ai-pos.project_analysis/v1",
  "project_path": "D:/path/to/project",
  "stage": "PLANNING",
  "confidence_state": "CONFIRMED",
  "stage_explanation": "Проект на стадии планирования: …",
  "what_is_present": ["PROJECT_CONTEXT.md", "ROADMAP.md"],
  "needs_attention": [],
  "next_step": { "text": "…", "action_hint": "…" },
  "analyzer": "project_analyzer_mvp_min",
  "project_files_top_level": [],
  "status": "ok",
  "valid": true,
  "notes": "Analyzer does not assign stage. Fields stage and confidence_state are copied from project_stage.json."
}
```

Неуспешный прогон (`valid: false`) — `invalidate_analysis`:

```json
{
  "schema": "ai-pos.project_analysis/v1",
  "project_path": "D:/path/to/project",
  "status": "invalid",
  "valid": false,
  "stage": null,
  "confidence_state": null,
  "error": "…",
  "invalidated_at": "2026-07-26T00:00:00Z",
  "analyzer": "project_analyzer_mvp_min"
}
```

Целевые поля вроде `stage_ref` / `summary` / `risks` / `soft_next_focus` в текущем MVP **не пишутся**.  
Правило границ: `next_step` в analysis для MVP берётся из stage (копия/адаптация Engine `next_step`), не как самостоятельное назначение стадии.

---

## 6. Границы ответственности (checklist)

| Действие | Stage Engine | project_analyzer |
|---|---|---|
| Выбрать `stage` | Да | Нет |
| Выставить `CONFIRMED` | Только по правилам Engine | Нет |
| Писать `project_stage.json` | Да | Нет |
| Писать `project_analysis.json` | Нет | Да |
| Объяснить стадию словами | Может дать evidence text | Да (`stage_explanation`) |
| Список присутствующих маркеров / внимания (MVP) | Нет | Да (`what_is_present`, `needs_attention`) |
| Блокировать Gate/Accept | Нет | Нет |
| Использовать GitHub evidence | Целевая модель Engine | MVP Analyzer не меняет stage |

---

## 7. Что не делать при развитии сверх MVP

1. Не удалять `tools/project_analyzer.py` «потому что есть Stage Engine».  
2. Не давать analyzer параметр `force_stage` / запись в stage file.  
3. Не сливать оба JSON в один «умный» отчёт с единым полем stage от ИИ.  
4. Не подменять MVP-контракт analysis целевыми полями без отдельного согласования границ.

---

## 8. Состояние реализации (факт)

Уже есть в репозитории:

1. `tools/project_stage_engine.py` — пишет `project_stage.json`.  
2. `tools/project_analyzer.py` — читает stage, пишет только `project_analysis.json`.  
3. `tools/refresh_project_insight.py` — Engine → Analyzer.  
4. `tools/mvp_smoke_check.py` — регрессия MVP-границ (analyzer не назначает stage).

Полная модель из `PROJECT_STAGE_ENGINE.md` (все стадии, GitHub-адаптер, Stage History) — целевая архитектура, не описание полноты текущего кода.

---

## 9. Открытые решения (узкие)

1. **TTL:** обязан ли analyzer всегда ждать свежий Engine-run или может читать stage не старше N минут?  

2. **Один процесс или два CLI?**  
   - Факт MVP: два модуля; оркестратор `refresh_project_insight.py` вызывает Engine → Analyzer.  

3. **Где живёт orchestrator в MVP?**  
   - Факт MVP: `tools/refresh_project_insight.py`; вызывается также из `tools/local_bridge.py`.
