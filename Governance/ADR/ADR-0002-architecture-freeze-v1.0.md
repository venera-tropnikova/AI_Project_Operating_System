# ADR-0002 — Architecture Freeze v1.0

Статус: **Accepted** · **ACTIVE**  
Дата: 2026-07-26  
Уточнение области (Baseline v0.1): 2026-07-27  
Pipeline: Observation → Hypothesis → Draft → Evidence → Candidate → Action Gate → **Accepted**

## Context

AI POS накопила архитектурные контуры: универсальный Intake & Discovery, Stage Engine, граница с `project_analyzer`, GitHub как evidence (не как назначение стадии), Orchestrator, Project Health UX/архитектура.  
Без Freeze границы размываются: анализатор начинает выбирать стадию, Health путается со Stage, Orchestrator становится «умным ядром», GitHub закрывает проекты без человека.

Для First MVP дополнительно зафиксирован временный Engineering Baseline (`docs/architecture/ARCHITECTURE_BASELINE_V0.1.md`). Без явной области Freeze Baseline легко принять за «объективную модель» или молча расширить.

## Decision

Вводится **Architecture Freeze v1.0**.  
Статус: **ACTIVE**.

До отдельного ADR о разморозке или частичном расширении Freeze:

1. Канонический Governance Pipeline:
   `Observation → Hypothesis → Draft → Evidence → Candidate → Action Gate → Accepted`.
2. Orchestrator — тонкий координатор (Engine → Analyzer); не источник истины о стадии.
3. Стадия проекта — только результат Stage Engine (`project_stage.json`); analyzer объясняет, не назначает; результаты разделены (`project_stage.json` / `project_analysis.json`).
4. GitHub и иные внешние системы — поставщики evidence, не прямые назначники стадии/accept.
5. Project Health в Freeze v1.0 имеет статус Governance **Observation** (не Draft и не Accepted), с тремя конкурирующими Hypothesis A/B/C (см. `HEALTH.md`).
   - **Supersede note (2026-07-27):** как *текущий* статус Project Health этот пункт superseded решением `DECISION_LOG` **D-2026-07-27-02**. Актуальный статус: **Draft** (основа Hypothesis C) — см. `Governance/HEALTH.md`, `Governance/PIPELINE.md`. Текст пункта 5 сохраняется как историческая фиксация Freeze v1.0; он не отменяет сам Architecture Freeze.
6. Architectural Observations #1–#3 зафиксированы как действующий журнал наблюдений.
7. Исполняющий ИИ не может единолично назначить `CONFIRMED`-стадию и не завершает Action Gate / Accepted.
8. **Область Freeze (уточнение 2026-07-27, Baseline v0.1):**
   - Governance Layer;
   - Architecture Baseline v0.1;
   - фундаментальные архитектурные допущения MVP (B-001–B-005 в Baseline).
9. **Freeze не запрещает:**
   - реализацию MVP;
   - исправление ошибок;
   - развитие Orchestrator, Analyzer, Local Bridge и UI в пределах Baseline;
   - создание Observation и сбор Evidence.
10. Изменение замороженной архитектуры допускается только через Governance Pipeline и Action Gate пользователя.

## Consequences

### Positive

- Одна каноническая лента принятия решений.  
- Снижен риск двойной истины о стадии.  
- Health не выдаётся за принятый модуль раньше времени.  
- Можно развивать analyzer и evidence-адаптеры без переписывания Freeze-ядра роли Orchestrator/Stage.  
- Baseline v0.1 явно помечен как Temporary / Experimental и не смешивается с истиной системы.

### Negative / trade-offs

- Новые крупные модули (полный Health Candidate, авто-delivery из GitHub) требуют явного прохода pipeline и, при необходимости, нового ADR.  
- Часть идей остаётся в Observation дольше, чем хотелось бы для скорости.  
- Экспериментальная стадия Validation описана в Baseline, но не входит в канон `PIPELINE.md` до MVP Retrospective.

## Out of Freeze (не разморожено этим ADR)

- Полная реализация кода Stage Engine / Orchestrator / Health.  
- Выбор единственной Health Hypothesis A/B/C как Accepted.  
- Автоматическое приравнивание GitHub Release к Accepted Delivery без user confirm.  
- Превращение Architecture Baseline v0.1 в постоянную «объективную модель» AI POS без Retrospective.

## Links

- `Governance/PIPELINE.md`  
- `Governance/ORCHESTRATOR.md`  
- `Governance/HEALTH.md`  
- `Governance/ARCHITECTURAL_OBSERVATIONS.md`  
- `Governance/DECISION_LOG.md` (в т.ч. **D-2026-07-27-03** — Baseline v0.1 / уточнение области Freeze; Action Gate пройден)  
- `docs/architecture/ARCHITECTURE_BASELINE_V0.1.md`  
- `research/evidence/MVP-001-EVIDENCE.md`
