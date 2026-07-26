# ADR-0002 — Architecture Freeze v1.0

Статус: **Accepted**  
Дата: 2026-07-26  
Pipeline: Observation → Hypothesis → Draft → Evidence → Candidate → Action Gate → **Accepted**

## Context

AI POS накопила архитектурные контуры: универсальный Intake & Discovery, Stage Engine, граница с `project_analyzer`, GitHub как evidence (не как назначение стадии), Orchestrator, Project Health UX/архитектура.  
Без Freeze границы размываются: анализатор начинает выбирать стадию, Health путается со Stage, Orchestrator становится «умным ядром», GitHub закрывает проекты без человека.

## Decision

Вводится **Architecture Freeze v1.0**.

До отдельного ADR о разморозке или частичном расширении Freeze:

1. Канонический Governance Pipeline:
   `Observation → Hypothesis → Draft → Evidence → Candidate → Action Gate → Accepted`.
2. Orchestrator — тонкий координатор (Engine → Analyzer); не источник истины о стадии.
3. Стадия проекта — только результат Stage Engine (`project_stage.json`); analyzer объясняет, не назначает; результаты разделены (`project_stage.json` / `project_analysis.json`).
4. GitHub и иные внешние системы — поставщики evidence, не прямые назначники стадии/accept.
5. Project Health в Freeze v1.0 имеет статус Governance **Observation** (не Draft и не Accepted), с тремя конкурирующими Hypothesis A/B/C (см. `HEALTH.md`).
6. Architectural Observations #1–#3 зафиксированы как действующий журнал наблюдений.
7. Исполняющий ИИ не может единолично назначить `CONFIRMED`-стадию и не завершает Action Gate / Accepted.

## Consequences

### Positive

- Одна каноническая лента принятия решений.  
- Снижен риск двойной истины о стадии.  
- Health не выдаётся за принятый модуль раньше времени.  
- Можно развивать analyzer и evidence-адаптеры без переписывания Freeze-ядра роли Orchestrator/Stage.

### Negative / trade-offs

- Новые крупные модули (полный Health Candidate, авто-delivery из GitHub) требуют явного прохода pipeline и, при необходимости, нового ADR.  
- Часть идей остаётся в Observation дольше, чем хотелось бы для скорости.

## Out of Freeze (не разморожено этим ADR)

- Полная реализация кода Stage Engine / Orchestrator / Health.  
- Выбор единственной Health Hypothesis A/B/C как Accepted.  
- Автоматическое приравнивание GitHub Release к Accepted Delivery без user confirm.

## Links

- `Governance/PIPELINE.md`  
- `Governance/ORCHESTRATOR.md`  
- `Governance/HEALTH.md`  
- `Governance/ARCHITECTURAL_OBSERVATIONS.md`  
- `Governance/DECISION_LOG.md`
