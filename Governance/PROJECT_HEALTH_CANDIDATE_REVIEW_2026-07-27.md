# Project Health — Candidate Readiness Review

**Дата:** 2026-07-27  
**Тип:** Candidate Readiness Review (Recommendation, не Decision)  
**Предмет:** зрелость Draft-контракта Project Health (Hypothesis C)  
**Статус Project Health после Review:** без изменений (остаётся Draft)

---

## 1. Scope

| Утверждение | Статус |
|---|---|
| Review относится только к Draft-спецификации и согласованности Governance | Да |
| Реализация Thin Health Layer / код / `project_health.json` не рассматриваются как условие этого Review | Да |
| Review **не** повышает статус Observation→Draft→Candidate автоматически | Да |
| Итог — **Recommendation** человеку, не Decision и не запись DECISION_LOG | Да |
| Orchestrator, Pipeline (кроме проверки факта), Analyzer, UI, Gate не изменяются этим Review | Да |

---

## 2. Проверка согласованности Governance

| # | Проверка | Факт | Источник | Результат |
|---|---|---|---|---|
| G1 | `HEALTH.md` = Draft | Статус: **Draft**; основа Hypothesis C | `Governance/HEALTH.md` строки статуса | **Passed** |
| G2 | `PIPELINE.md` = Draft (Hypothesis C) | Таблица контура: `Draft (Hypothesis C); D-2026-07-27-02` | `Governance/PIPELINE.md` | **Passed** |
| G3 | D-2026-07-27-02 соответствует статусу | Решение: Hypothesis C; HEALTH → Draft; индикаторы/код не утверждены | `Governance/DECISION_LOG.md` D-02 | **Passed** |
| G4 | Draft-спека не противоречит Constitution П.2 / П.3 | Facts vs interpretation; Analyzer не SSOT Health | `PROJECT_HEALTH_DRAFT_SPEC` §2–3, §7–8; CONSTITUTION | **Passed** |
| G5 | Согласованность Stage / Analyzer | Stage truth vs analysis; Health не назначает stage | Draft Spec §3–4; D-2026-07-26-02; Boundary | **Passed** |
| G6 | Evidence / Accept | Health ≠ Accepted; evidence ≠ Accept | Draft Spec §2, §8; Observation #2 | **Passed** |
| G7 | Action Gate | Health не заменяет Gate; non-goals без блокировок | Draft Spec §4, §8–9; CHANGE_PROTOCOL / PIPELINE | **Passed** |
| G8 | Doc-drift статуса Health устранён в оперативных docs | HEALTH + PIPELINE + D-02 согласованы на Draft | См. G1–G3 | **Passed** |
| G9 | Оставшийся drift | ADR-0002 п.5 всё ещё: Health = **Observation** (+ A/B/C) | `Governance/ADR/ADR-0002-…md` | **Partial** |
| G10 | Внутренняя актуальность Evidence в Draft Spec | §11.1 E9 всё ещё помечен **Failed** (текст про старый PIPELINE), хотя PIPELINE уже синхронизирован (коммит `bc51641`) | `PROJECT_HEALTH_DRAFT_SPEC` §11.1 vs `PIPELINE.md` | **Failed** (устаревшая фиксация внутри Draft Spec) |
| G11 | Workshop / CHANGE_PROTOCOL | Workshop — основание выбора C; CHANGE_PROTOCOL допускает перевод Health Draft→Candidate как значимое | Workshop; CHANGE_PROTOCOL §3 | **Passed** (процесс) |

---

## 3. Проверка границ Hypothesis C

| Правило | Подтверждение | Риск нарушения | Статус |
|---|---|---|---|
| Thin Health Layer = только facts | Draft Spec §3.1, §6 (нет narrative/recommendation/stage) | Срыв в narrative fields при реализации | **Passed** (контракт) |
| Analyzer = interpretation | Draft Spec §3.2, §7; `needs_attention` в analysis | Выдать analysis за Health truth | **Passed** (контракт) |
| Health не назначает Stage | §6 запрет `stage`; §4 Stage Engine | Копирование `stage` в health file | **Passed** (контракт) |
| Health не объявляет Accepted | §2, §8; Observation #2 | UI «зелёный Health» = сдано | **Passed** (контракт) |
| Health не заменяет Gate | §4, §8–9 | Агрегат critical → lock | **Passed** (контракт); runtime N/A |
| Health не зависит от `project_analysis.json` | Источники H-IND = `project_stage.json` / presence; §7 analysis читает Health, не наоборот | Реализация читает analysis для indicators | **Passed** (контракт) |
| Analyzer не SSOT Health | П.3; Hypothesis C; §3.2 | B-срыв | **Passed** (контракт) |
| `/api/health` ≠ Project Health | `local_bridge.py` do_GET: только `ok`/`service`/`orchestrator`; нет чтения health artifacts | Переиспользование URL | **Passed** (код + контракт) |
| `needs_attention` ≠ Health indicator | Нет H-IND id `needs_attention`; HEALTH.md §3; analyzer поле | Алиас при реализации | **Passed** (контракт) |

---

## 4. Review индикаторов H-IND-01…05

**Факт oracle (ручной пересчёт из текущих `project_stage.json`, 2026-07-27):**

| Indicator | TEMPLATE | mini_filled |
|---|---|---|
| `stub_documents_present` | true, count=6 | false, count=0 |
| `stage_blockers_present` | true, count=1 | false, count=0 |
| `conflicting_stage_evidence_present` | false | false |
| `stage_snapshot_stale_flag` | false | false |
| `substantive_context_absent` | true | false |

Источники: `Projects/TEMPLATE/.ai-pos/project_stage.json` (`stub_files`×6, `blockers`×1, `context_hits`=[], `stale=false`); `Projects/FIXTURES/mini_filled/.ai-pos/project_stage.json` (`stub_files`=[], `blockers`=[], `context_hits`=[PROJECT_CONTEXT.md], `stale=false`).

### 4.1. Сводка по индикаторам

| ID | Источник есть | Детерминизм | Без narrative | Без NL Stage text | Не новая истина Stage | Польза для Health | Тест TEMPLATE/mini | Статус Review |
|---|---|---|---|---|---|---|---|---|
| H-IND-01 | `presence.stub_files` | Да | Да | Да (имена файлов — structural) | Да (проекция presence) | Да — полнота документов | Да (6 vs 0) | **Ready for v0** |
| H-IND-02 | `blockers` | Да | Да | Да (см. §4.2) | Да (boolean/count + ref) | Да — есть ли stage blockers | Да (1 vs 0) | **Ready for v0** |
| H-IND-03 | `conflicting_evidence` | Да | Да | Да | Да | Да — конфликт evidence | Да (оба false) | **Ready for v0** |
| H-IND-04 | `source_freshness.stale` | Да | Да | Да | См. §4.3 | Условная | Да (оба false) | **Ready with caveat** |
| H-IND-05 | `presence.context_hits` | Да | Да | Да | Да (отсутствие context hits) | Да — нет содержательного context | Да (true vs false) | **Ready for v0** |

### 4.2. H-IND-02 — подтверждение

| Требование | Факт в Draft Spec |
|---|---|
| Только boolean/count | Да: `false\|true`; опционально `count` |
| Structural references `{path, field}` | Да: `.ai-pos/project_stage.json` / `blockers` |
| Нет копирования blockers text / `texts[]` | Да: запрет NL; `texts[]` отсутствует |
| Одна строка «Способ вычисления» | Да: `len(blockers) > 0`; опционально `count = len(blockers)` |

**Результат:** **Passed**.

### 4.3. H-IND-04 — проекция или лишнее зеркало?

| Вопрос | Оценка Review |
|---|---|
| Допустимая проекция факта Stage? | **Да.** `source_freshness.stale` уже в контракте Engine; Health копирует boolean, не текст. |
| Самостоятельная ценность для Health? | **Частичная.** Смысл Health: «оцениваем ли состояние по свежему снимку стадии». На текущих фикстурах оба `false` — различительная сила на TEMPLATE vs mini_filled **нулевая**. |
| Лишнее зеркалирование? | Риск есть, если UI просто дублирует stale рядом со Stage без вопроса «можно ли доверять остальным Health facts». |

**Recommendation (не Decision):** сохранить H-IND-04 в v0 как **optional/low-weight** indicator (boolean + reference), не удалять; не строить на нём агрегат; пересмотреть ценность после Evidence с реальным `stale=true`.

---

## 5. Проверка открытых вопросов Q1–Q6

| Q | Суть | Обязательно до Candidate? | Можно оставить открытым в Candidate? | Отдельное arch-решение? | Недостающие Evidence |
|---|---|---|---|---|---|
| Q1 | Имя/путь артефакта (`project_health.json`) | **Да** для закрытого контракта Candidate | Нет как «навсегда TBD» | Да (именование схемы) | Согласование с `.ai-pos/` naming |
| Q2 | Обязательный набор H-IND-01…05 | **Да** (freeze v0 set) | Нет | Да (состав v0) | Oracle выше; executable later |
| Q3 | `health_level` ok/attention/critical | **Не включать в v0** (см. ниже) | Да — вне v0 | Да, если позже вводить | UX-сценарий отсутствует |
| Q4 | Порядок в Orchestrator | Нет для Candidate **контракта** | **Да** до реализации | Да перед кодом Orchestrator | Влияние на NORMAL/DIAGNOSTIC |
| Q5 | `project_id` vs path | Нет | **Да** (MVP = path) | Только если появится multi-root | Кейсы переноса папок |
| Q6 | Sync PIPELINE/ADR | PIPELINE **сделан**; ADR остаётся | ADR sync — до/параллельно Candidate | Doc-sync ADR | Текст ADR п.5 |

### Q3 — aggregated `health_level` (Recommendation Workshop Review)

**Recommendation (не Decision человека):**

- **не** включать `health_level` в v0 Candidate-контракт;
- **не** использовать шкалу ok / attention / critical в Thin Health Layer v0;
- вернуть вопрос в Observation **только** при появлении реального пользовательского сценария (потребность агрегата доказана Evidence), а не по умолчанию.

Опора: Draft Spec Q3 / H-IND-R01; риск подмены Gate и паники UI (`PROJECT_STAGE_ENGINE` UX note); D-02 не утверждал агрегат.

---

## 6. Evidence Status E1–E9

| Evidence | Текущий статус | Что уже подтверждено | Что ещё требуется |
|---|---|---|---|
| E1 | **Passed** | Контракт: нет назначаемого `stage`; запрет NL Stage | Executable тест после реализации (не блокер Candidate-контракта) |
| E2 | **Manual oracle established** | TEMPLATE oracle: stubs=6, blockers=1, conflict=false, stale=false, context_absent=true | Executable verification pending implementation |
| E3 | **Manual oracle established** | mini_filled oracle: stubs=0, blockers=0, conflict=false, stale=false, context_absent=false | Executable verification pending implementation |
| E4 | **Pending implementation** | Контракт: Analyzer не мутирует Health facts | Runtime-тест после появления artifact |
| E5 | **Passed** | Нет indicator id `needs_attention`; поле Analyzer исключено | Code review при реализации |
| E6 | **Passed** | `local_bridge.py`: `/api/health` = liveness only; Health artifacts не читает | Не смешивать URL при будущих API |
| E7 | **Not applicable** | UI Health facts отсутствует | UI review при появлении UI |
| E8 | **Partial** | Спека запрещает Gate lock; Health lock API нет | Проверка после любого агрегата/UI |
| E9 | **Passed** (актуальное состояние репо) | `PIPELINE.md` = Draft (Hypothesis C); D-02; HEALTH.md = Draft | **Исправить устаревший Failed в Draft Spec §11.1**; **ADR-0002** всё ещё Observation (**Partial** drift) |

**Ожидаемые значения (manual oracle) — зафиксированы:**

| Indicator | TEMPLATE | mini_filled |
|---|---|---|
| stub_documents_present | true, count=6 | false, count=0 |
| stage_blockers_present | true, count=1 | false, count=0 |
| conflicting_stage_evidence_present | false | false |
| stage_snapshot_stale_flag | false | false |
| substantive_context_absent | true | false |

E2/E3 **не** названы полностью **Passed** (нет исполняемой проверки).

---

## 7. Candidate Entry Criteria

**Смысл Candidate здесь:** готовность **контракта** к последующей реализации, не наличие кода (ALIGN с D-02 / Draft Spec non-goals).

### 7.1. Должно быть решено до Candidate

1. Freeze v0 indicator set: H-IND-01…05 (с политикой H-IND-04 optional/low-weight — по решению человека).  
2. Freeze имени/размещения артефакта (принять Draft-предложение `.ai-pos/project_health.json` + schema id **или** явную альтернативу).  
3. Явно исключить `health_level` из v0 (или явно включить — требует отдельного решения; Review рекомендует исключить).  
4. Устранить внутренний drift Draft Spec §11.1 E9 (текст Failed → актуальное Passed по PIPELINE).  
5. Устранить или явно supersede ADR-0002 п.5 (Observation → указание на D-02 / Draft).

### 7.2. Разрешено оставить открытым в Candidate

- Q4 — порядок Orchestrator (решить до кода Orchestrator).  
- Q5 — `project_id` (MVP path).  
- Executable E2/E3/E4 (после реализации).  
- E7 UI.  
- Полная E8 после UI/агрегатов.  
- Research indicators H-IND-R02…R05.

### 7.3. Запрещено до Accepted

- Считать Health источником Stage / Accept / Gate.  
- Автоматические блокировки по Health.  
- Подмена `needs_attention` / `/api/health` за Project Health.  
- Полный Health Engine (Hypothesis A) без нового pipeline.  
- Реализация **без** явного разрешения человека после Candidate (Candidate ≠ разрешение кода само по себе; код — отдельное решение).

---

## 8. Блокирующие замечания

**Жёстких blockers, делающих рассмотрение Candidate невозможным, нет:** оперативные Governance-источники (HEALTH, PIPELINE, D-02) согласованы; границы Hypothesis C в контракте выдержаны; oracle E2/E3 установлен вручную.

Условия §7.1 — **входные критерии**, не «невозможность Review». Они перечислены как обязательные fixes/решения **перед** переводом, не как отказ от Recommendation.

---

## 9. Неблокирующие замечания

| # | Замечание |
|---|---|
| N1 | Обновить Draft Spec §11.1 E9 (устаревший Failed) при следующем micro-edit спеки. |
| N2 | ADR-0002 п.5 — исторический Freeze-текст; нужен supersede/note без переписывания всего ADR. |
| N3 | H-IND-04 слабо различает текущие фикстуры; держать optional. |
| N4 | Workshop F1 исторически говорит Observation — нормально для архива Workshop. |
| N5 | CHANGE_PROTOCOL формулировка «из Observation в Draft/Candidate» остаётся валидной для следующих переходов. |

---

## 10. Recommendation

### **Recommend Candidate after specified fixes**

**Обоснование (Evidence):**

- **За:** G1–G8 Passed; границы §3 Passed на уровне контракта; H-IND-01…05 опираются на существующие stage facts; H-IND-02 Passed; E1/E5/E6 Passed; E2/E3 Manual oracle established; E9 репозитория Passed после sync PIPELINE; реализация по Governance не обязательна для Candidate-контракта.  
- **Против немедленного «Recommend Candidate» без оговорок:** G10 Failed (устаревший E9 внутри Draft Spec); G9 Partial (ADR Observation); Q1/Q2 не freeze; Q3 должен быть явно исключён из v0 решением человека.

**Specified fixes / решения человека перед переводом в Candidate:**

1. Micro-edit Draft Spec: §11.1 E9 → актуальное **Passed** (PIPELINE синхронизирован).  
2. Doc-sync или supersede-note для ADR-0002 п.5 → Draft / D-02.  
3. Явный freeze: имя артефакта v0 + набор H-IND-01…05 (+ политика H-IND-04) + исключение `health_level` из v0 (если человек согласен с Recommendation по Q3).

После выполнения пунктов 1–3 человек может принять Decision о переводе Draft→Candidate через pipeline / DECISION_LOG.

Этот Review **не** утверждает Candidate и **не** меняет статус.

---

## 11. Следующий разрешённый шаг

Человеку:

1. Рассмотреть Recommendation §10.  
2. Принять или отклонить путь «Candidate after specified fixes».  
3. При согласии — поручить точечные исправления §10 (1–3), затем отдельным явным решением рассмотреть перевод в Candidate (DECISION_LOG / статус HEALTH — только по поручению человека).  

**Реализация Thin Health Layer / код / Orchestrator — не разрешены** этим Review.

---

Candidate Readiness Review завершён.

Recommendation не является архитектурным решением.

Статус Project Health не изменён.

Реализация не разрешена.

Ожидается явное решение человека.
