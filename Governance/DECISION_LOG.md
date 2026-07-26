# DECISION_LOG

Статус: Active  
Версия контура: Architecture Freeze v1.0

Журнал принятых и ключевых управленческих решений.  
Записи не удаляются; устаревшие помечаются Superseded.

---

## D-2026-07-26-01 — Architecture Freeze v1.0

- **Статус:** Accepted  
- **ADR:** ADR-0002  
- **Pipeline:** … → Action Gate → Accepted  
- **Решение:** Введён Architecture Freeze v1.0; канонизирован Governance Pipeline; Orchestrator принят как тонкий координатор; Health зафиксирован как Observation с Hypothesis A/B/C; зафиксированы Architectural Observations #1–#3.  
- **Не решает:** выбор единственной Health Hypothesis; полная кодовая реализация модулей.

---

## D-2026-07-26-02 — Разделение stage и analysis

- **Статус:** Accepted (в составе Freeze v1.0)  
- **Решение:** `project_stage.json` — фактическая стадия (Stage Engine); `project_analysis.json` — аналитическая сводка (project_analyzer). Analyzer не выбирает стадию.  
- **Связь:** ORCHESTRATOR.md, Observation #1

---

## D-2026-07-26-03 — Восстановление Конституции на 10 принципов

- **Дата:** 2026-07-26  
- **Статус:** Accepted  
- **Что изменено:**
  - `Governance/CONSTITUTION.md` восстановлен как канон с ровно 10 принципами;
  - `.cursor/rules/ai-pos-constitution.mdc` синхронизирован с каноном;
  - `.cursor/rules/ai-pos-user-first.mdc` зафиксирован как производное правило (не высший принцип над Конституцией).
- **Причина:** Конституция была пересмотрена после проверки принципов на независимость от реализации. Обобщённые продуктовые нормы не заменяют архитектурные инварианты. Были восстановлены принципы, сохраняющие силу при смене технологий, моделей ИИ, интерфейсов и исполнителей. Brand Consistency и Simplicity оставлены на уровне Standards, а не Конституции.
- **Последствия:**
  - главным объектом системы является проект;
  - Orchestrator остаётся диспетчером, а не судьёй;
  - человек сохраняет Action Gate и Accepted;
  - производные правила Cursor подчиняются `Governance/CONSTITUTION.md`;
  - изменение не затрагивает код и действующий Architecture Freeze v1.0.
- **Связанные документы:** `Governance/CONSTITUTION.md`, `.cursor/rules/ai-pos-constitution.mdc`, `.cursor/rules/ai-pos-user-first.mdc`, ADR-0002, `PIPELINE.md`

---

## D-2026-07-26-04 — Подпись UI для `project.stage`

- **Дата:** 2026-07-26  
- **Статус:** Accepted  
- **Решение:**
  - `project.stage` остаётся локальным рабочим состоянием карточки проекта в UI;
  - подпись поля в интерфейсе: «Текущая работа»;
  - Stage Engine остаётся единственным источником истины о системной стадии проекта.
- **Связанные документы:** `index.html`, `Governance/ARCHITECTURAL_OBSERVATIONS.md` (#4)

---

## D-2026-07-27-01 — Удаление незачартёренного scaffold `Procedures/`

- **Дата:** 2026-07-27  
- **Статус:** Accepted  
- **Что установлено аудитом:**
  - проведён архитектурный аудит слоя `Procedures/`;
  - подтверждено отсутствие принятого решения об учреждении этого слоя (нет в CONSTITUTION, PIPELINE, CHANGE_PROTOCOL, ADR, DECISION_LOG);
  - каталог признан неиспользуемым initial scaffold: пустые Draft-файлы без содержания, ссылок и архитектурной ответственности.
- **Решение:** удалить scaffold слоя `Procedures/` целиком.
- **Повторное введение:** слой `Procedures` может быть введён только через обычный Governance Pipeline (`Observation → Hypothesis → Draft → … → Action Gate → Accepted`).
- **Не затрагивает:** Architecture Freeze v1.0 (ADR-0002); канон Action Gate в `PIPELINE.md` / `CHANGE_PROTOCOL.md`; CONSTITUTION и прочие Accepted-контуры.
