# Project Health — Candidate Decision Package

**Дата:** 2026-07-27  
**Тип:** Decision Package (упаковка материалов для Human Decision)  
**Статус пакета:** подготовлен; **Human Decision не принят** этим файлом  
**Статус модуля Project Health:** остаётся **Draft** (Hypothesis C), пока человек не примет иное решение

Этот документ **не** изменяет `HEALTH.md`, `DECISION_LOG`, `PIPELINE.md`, ADR и код.  
Он только собирает уже существующие артефакты для рассмотрения перевода Draft → Candidate.

---

## 1. Основание (самодостаточное)

Основание Human Decision по Candidate — следующие **репозиторные** материалы и зафиксированные в них выводы (без ссылок на переписку).

### 1.1. Принятое решение о Draft

| Элемент | Содержание | Источник |
|---|---|---|
| Решение | Hypothesis **C** — основа Draft Project Health; `HEALTH.md` → Draft | `DECISION_LOG` **D-2026-07-27-02** (Accepted) |
| Нормы | Constitution Principle 2; Stage/Analyzer; Evidence/Accept; Observation #4 (Конституция = норма, Health = 3-е применение) | D-2026-07-27-02 §Основание |
| Не решено D-02 | Спецификация индикаторов; код; перевод в Candidate/Accepted | D-2026-07-27-02 |

### 1.2. Workshop (выбор Hypothesis)

| Элемент | Содержание | Источник |
|---|---|---|
| Recommendation Workshop | Рассмотреть Hypothesis C как основу Draft | `HEALTH_DECISION_WORKSHOP_2026-07-27.md` §6 R4 |
| Итог для человека (исполнен) | C принята в D-2026-07-27-02 | DECISION_LOG; `HEALTH.md` |

**Резюме модели C (из Workshop / HEALTH.md):** тонкий фактологический слой индикаторов/отчёта + интерпретация в Analyzer; не назначает Stage; не заменяет Gate/Accept.

### 1.3. Draft Specification

| Элемент | Содержание | Источник |
|---|---|---|
| Контракт Draft | Thin Health Layer (facts) vs Analyzer (interpretation); non-goals; коллизии `/api/health`, `needs_attention` | `PROJECT_HEALTH_DRAFT_SPEC_2026-07-27.md` |
| H-IND-02 (актуальная редакция) | boolean / `count`; structural reference `{path, field}`; **без** копирования NL Stage / без `texts[]` | Draft Spec §5.1 H-IND-02 |
| Имя артефакта | Draft-предложение `.ai-pos/project_health.json` — **не утверждено** отдельным решением | Draft Spec §6 |
| Реализация | Не разрешена документом Draft Spec | Draft Spec §9, §12 |

### 1.4. Candidate Readiness Review

| Элемент | Содержание | Источник |
|---|---|---|
| Recommendation Review | **Recommend Candidate after specified fixes** | `PROJECT_HEALTH_CANDIDATE_REVIEW_2026-07-27.md` §10 |
| Жёсткие blockers | Нет | Candidate Review §8 |
| Входные критерии до Candidate | Freeze v0 индикаторов и имени артефакта; исключение `health_level` из v0 (рекомендация Review); micro-edit E9 в Draft Spec; sync/supersede ADR-0002 п.5 | Candidate Review §7.1, §10 |
| Открыто после входа в Candidate | Порядок Orchestrator (Q4); `project_id` (Q5); executable E2/E3/E4; UI (E7) | Candidate Review §7.2 |
| Запрещено до Accepted | Health ≠ Stage/Accept/Gate; нет авто-блокировок; Candidate ≠ авторазрешение кода | Candidate Review §7.3 |

**Резюме Evidence (из Candidate Review §6):** E1/E5/E6 Passed; E2/E3 Manual oracle established; E4 Pending implementation; E7 Not applicable; E8 Partial; E9 репозитория Passed (`PIPELINE.md` = Draft), при устаревшей пометке Failed внутри Draft Spec §11.1.

**Manual oracle (из Candidate Review §4 / §6):**

| Indicator | TEMPLATE | mini_filled |
|---|---|---|
| stub_documents_present | true, count=6 | false, count=0 |
| stage_blockers_present | true, count=1 | false, count=0 |
| conflicting_stage_evidence_present | false | false |
| stage_snapshot_stale_flag | false | false |
| substantive_context_absent | true | false |

### 1.5. Оперативный статус в Governance

| Документ | Факт |
|---|---|
| `HEALTH.md` | Статус **Draft**; основа Hypothesis C |
| `PIPELINE.md` | Project Health = `Draft (Hypothesis C); D-2026-07-27-02` |
| ADR-0002 п.5 | Текст всё ещё Observation (+ A/B/C) — отмечено Candidate Review как Partial drift |

---

## 2. Recommendation (не решение)

Архитектурная Recommendation (не Human Decision):

**Рекомендуется вариант A** — путь *Candidate after specified fixes*.

Опора: Candidate Readiness Review §10; Decision Package §1.

Этот раздел **не** принимает решение за человека.

---

## 3. Specified fixes (из Candidate Review §10) — условие варианта A

Если человек **подтверждает** Recommendation (вариант A), перед записью Candidate должны быть закрыты:

1. Micro-edit Draft Spec: §11.1 E9 → актуальное **Passed** (PIPELINE уже синхронизирован).  
2. Doc-sync или supersede-note для ADR-0002 п.5 → Draft / D-2026-07-27-02.  
3. Явный freeze: имя артефакта v0 + набор H-IND-01…05 (+ политика H-IND-04 optional/low-weight) + исключение `health_level` из v0 (если человек согласен с Recommendation Review по Q3).

---

## 4. Что уже зафиксировано (не пересматривается этим пакетом)

| Утверждение | Источник |
|---|---|
| Hypothesis C — основа Draft | D-2026-07-27-02 |
| Thin facts ≠ Analyzer interpretation | Draft Spec; Workshop; D-02 |
| H-IND-02: count + structural reference, без NL-text | Draft Spec §5.1 |
| Реализация / `project_health.json` в runtime не разрешены пакетом | Draft Spec; Candidate Review |
| Candidate ≠ Accepted; нужен дальнейший pipeline | PIPELINE; CHANGE_PROTOCOL; Candidate Review §7.3 |

---

## 5. Что пакет явно не делает

- Не записывает `DECISION_LOG`.  
- Не меняет статус `HEALTH.md` / `PIPELINE.md`.  
- Не изменяет ADR-0002.  
- Не утверждает Candidate.  
- Не разрешает код, Orchestrator, UI, Gate locks.  
- Не вводит новых гипотез или индикаторов сверх Draft Spec / Candidate Review.  
- Не подменяет Human Decision формой ниже.

---

## 6. Форма Human Decision (заполняет человек)

**Готовность:** Project Health готов к Human Decision.  
**Предмет:** подтвердить или отклонить Recommendation (§2) о варианте A.

Отметить **ровно один** вариант.

Коды формы **не** связаны с Hypothesis A/B/C.

| Отметка | Код | Формулировка |
|---|---|---|
| [ ] | **APPROVE** | **Подтверждаю** Recommendation: путь *Candidate after specified fixes*. После выполнения §3 — отдельная запись Candidate в DECISION_LOG / `HEALTH.md` по явному поручению. |
| [ ] | **REJECT** | **Отклоняю** Recommendation / перевод в Candidate на текущем основании. Статус остаётся Draft. |
| [ ] | **DEFER** | **Откладываю** решение. Статус остаётся Draft. |

### 6.1. Реквизиты

| Поле | Значение (заполняет человек) |
|---|---|
| Дата | |
| Выбранный код (`APPROVE` / `REJECT` / `DEFER`) | |
| Подпись / фиксация | |

### 6.2. Только при APPROVE — подтверждение freeze v0

| Параметр | Решение человека |
|---|---|
| Имя/путь артефакта v0 (предложение Draft Spec: `.ai-pos/project_health.json` — принять / иное) | |
| Набор H-IND-01…05 в v0 (да / с оговорками) | |
| H-IND-04 optional/low-weight (да / нет) | |
| `health_level` исключён из v0 (да / нет) | |

### 6.3. Фиксация результата формы

| Утверждение | Да / Нет |
|---|---|
| Human Decision по этой форме принят | |
| Статус Project Health изменён этой формой | **Нет** (изменение статуса — только отдельным шагом после APPROVE и §3) |
| Реализация разрешена этой формой | **Нет** |

---

## 7. Индекс источников

| # | Путь | Роль в пакете |
|---|---|---|
| S1 | `Governance/DECISION_LOG.md` (D-2026-07-27-02) | Accepted решение Draft / Hypothesis C |
| S2 | `Governance/HEALTH.md` | Текущий статус Draft |
| S3 | `Governance/PIPELINE.md` | Статус контура Draft (Hypothesis C) |
| S4 | `Governance/HEALTH_DECISION_WORKSHOP_2026-07-27.md` | Workshop Recommendation → C |
| S5 | `Governance/PROJECT_HEALTH_DRAFT_SPEC_2026-07-27.md` | Draft-контракт, индикаторы, non-goals |
| S6 | `Governance/PROJECT_HEALTH_CANDIDATE_REVIEW_2026-07-27.md` | Candidate Readiness Review + Recommendation |
| S7 | `Governance/CONSTITUTION.md` | Principle 2 / 3 (через D-02 / Workshop) |
| S8 | `Governance/ADR/ADR-0002-architecture-freeze-v1.0.md` | Freeze; п.5 — drift vs Draft (факт Review) |

---

Decision Package подготовлен.

Форма Human Decision готова (§6).

Human Decision не принят.

Статус Project Health не изменён.

Реализация не разрешена.

Project Health готов к Human Decision: человеку достаточно заполнить §6 (APPROVE / REJECT / DEFER).
