# Architecture Baseline v0.1

| Field | Value |
|---|---|
| Document Type | Architecture Baseline |
| Status | Experimental |
| Purpose | Support First MVP |
| Version | 0.1 |
| Lifecycle State | Temporary |
| Expected Lifetime | Until MVP Retrospective |
| Architecture Freeze | Active |

Связь: `Governance/CONSTITUTION.md`, `Governance/ADR/ADR-0002-architecture-freeze-v1.0.md`, `Governance/DECISION_LOG.md` (**D-2026-07-27-03**, Accepted), `Governance/PIPELINE.md`, `research/evidence/MVP-001-EVIDENCE.md`

---

## Role in AI POS

Architecture Baseline — временный инженерный ориентир первого MVP.

Он поддерживает согласованную разработку, пока действует Architecture Freeze, и не заменяет Конституцию, ADR или Accepted-контур Governance.

---

## Цель документа

Зафиксировать текущее инженерное понимание AI POS, достаточное для First MVP:

- что считается объектом управления;
- какие допущения считаются рабочими;
- что заморожено;
- как собираются факты для ретроспективы.

---

## Architecture Baseline ≠ Truth

**Architecture Baseline фиксирует текущее инженерное понимание системы, а не объективную модель AI POS.**

Baseline:

- не объявляет окончательную истину о системе;
- не расширяет Accepted-архитектуру сам по себе;
- может быть подтверждён, переработан или снят на Architecture Retrospective после MVP.

---

## Главная цель AI POS

**Главным объектом системы является проект.**

**AI POS управляет выполнением проекта посредством управления жизненным циклом инженерных артефактов.**

Компоненты (Orchestrator, Analyzer, Local Bridge, UI и др.) существуют для обслуживания жизненного цикла проекта, а не наоборот.

---

## Рабочие архитектурные допущения B-001–B-005

Допущения Baseline — рабочие опоры MVP. Они не являются новой Accepted-архитектурой вне уже принятого контура; изменение формулировок после Freeze — только через Governance Pipeline и Action Gate.

| ID | Допущение | Опора в принятом контуре |
|---|---|---|
| **B-001** | Главным объектом системы является проект. | Constitution, принцип 10 |
| **B-002** | AI POS управляет выполнением проекта посредством управления жизненным циклом инженерных артефактов. | Цель Baseline / First MVP |
| **B-003** | Нормы и факты разделяются; системная стадия проекта не назначается аналитикой или ИИ единолично. | Constitution, принципы 2 и 3; ADR-0002 |
| **B-004** | Orchestrator — тонкий координатор, а не источник истины о стадии, здоровье или правилах. | ADR-0002; `Governance/ORCHESTRATOR.md` |
| **B-005** | Человек сохраняет Action Gate и Accepted; значимые изменения архитектуры идут через Governance Pipeline. | Constitution; `Governance/PIPELINE.md`; ADR-0002 |

---

## Architecture Freeze

**Architecture Freeze v1.0: ACTIVE**

Область Freeze в рамках Baseline v0.1:

- Governance Layer;
- Architecture Baseline v0.1;
- фундаментальные архитектурные допущения MVP (B-001–B-005).

Freeze **не запрещает**:

- реализацию MVP;
- исправление ошибок;
- развитие Orchestrator, Analyzer, Local Bridge и UI в пределах Baseline;
- создание Observation и сбор Evidence.

Изменение замороженной архитектуры допускается только через Governance Pipeline и Action Gate пользователя.

Каноническая фиксация: `Governance/ADR/ADR-0002-architecture-freeze-v1.0.md`, запись в `Governance/DECISION_LOG.md`.

---

## Governance Pipeline

Для First MVP Baseline использует последовательность:

```text
Observation
→ Hypothesis
→ Draft
→ Evidence
→ Candidate
→ Validation
→ Action Gate
→ Accepted
```

Канонический Accepted-pipeline Freeze v1.0 в `Governance/PIPELINE.md` на момент Baseline **не содержит** стадию Validation. Baseline не переписывает канон молча: Validation описан ниже как экспериментальный элемент MVP.

---

## Экспериментальный статус Validation

**Validation** включён в ленту Baseline **экспериментально**.

По итогам первого MVP Validation должен быть:

- подтверждён как постоянная стадия канона, **или**
- переработан, **или**
- исключён.

До ретроспективы Validation не считается окончательной нормой Конституции / `PIPELINE.md`.

---

## Research

Research в контуре First MVP — сбор проверяемых фактов о том, как Baseline помогает или мешает разработке.

Рабочий журнал: `research/evidence/MVP-001-EVIDENCE.md`.

Observation не становится архитектурным решением автоматически.

---

## Architecture Retrospective

Ожидаемый горизонт жизни Baseline — до **MVP Retrospective**.

На ретроспективе по Evidence Log и фактам MVP принимается решение:

- сохранить / уточнить допущения B-001–B-005;
- подтвердить, переработать или исключить Validation;
- снять или заменить Temporary Baseline.

---

## Критерий успешности Baseline

Baseline v0.1 успешен, если за время First MVP:

1. разработка опиралась на явные допущения B-001–B-005 без скрытого переписывания Freeze;
2. факты о помощи / помехах архитектуры регулярно попадали в Evidence Log;
3. MVP Retrospective может принять решение о судьбе Baseline и Validation на основании записанных фактов, а не впечатлений.

---

## Observation об Engineering Artifact

**Observation (не решение):** инженерный артефакт — рабочая единица, через жизненный цикл которой AI POS ведёт выполнение проекта (B-002).

Это наблюдение Baseline для MVP. Оно **не** учреждает отдельный Accepted-модуль и **не** заменяет Конституцию. Дальнейшая проработка — только через Governance Pipeline при наличии Evidence.

---

## Статус исследования

| Элемент | Статус |
|---|---|
| Architecture Baseline v0.1 | Experimental / Temporary |
| Architecture Freeze v1.0 | Active |
| Evidence Log MVP-001 | Active (стартовый журнал; пустые шаблоны ≠ Evidence) |
| Validation (стадия pipeline) | Experimental — решение после MVP Retrospective |
| Engineering Artifact | Observation only |
