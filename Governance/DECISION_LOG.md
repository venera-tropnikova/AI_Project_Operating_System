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

---

## D-2026-07-27-02 — Project Health: Hypothesis C как основа Draft

- **Дата:** 2026-07-27  
- **Статус:** Accepted  
- **Pipeline:** Observation → Hypothesis (выбор C) → вход в Draft  
- **Решение:**
  - человек рассмотрел Recommendation Decision Workshop (`Governance/HEALTH_DECISION_WORKSHOP_2026-07-27.md`);
  - Recommendation признана обоснованной;
  - выбрана Hypothesis **C** (гибридная модель) как основа Draft Project Health;
  - `Governance/HEALTH.md` переводится из Observation в **Draft** на этой основе.
- **Основание:**
  - Constitution Principle 2 (нормы и факты разделяются);
  - предметное применение Stage / Analyzer (факт стадии vs интерпретация);
  - предметное применение Evidence / Accept;
  - методологически исправленный Observation #4 (Конституция — нормативный источник; Project Health — третье применение оси «факты / интерпретация»);
  - Decision Workshop 2026-07-27.
- **Не решает:** спецификацию индикаторов; код Health; перевод в Candidate/Accepted; изменение PIPELINE.md.
- **Связанные документы:** `Governance/HEALTH.md`, `Governance/HEALTH_DECISION_WORKSHOP_2026-07-27.md`, `Governance/CONSTITUTION.md`, ADR-0002

---

## D-2026-07-27-03 — Architecture Baseline v0.1 и уточнение области Freeze

- **Дата:** 2026-07-27  
- **Статус:** Accepted  
- **Pipeline:** … → Action Gate → Accepted  
- **Action Gate:** пройден человеком (Human Decision; зафиксировано 2026-07-28)  
- **ADR:** ADR-0002 (уточнение; Freeze остаётся **ACTIVE**)  
- **Решение:**
  - введён временный документ `docs/architecture/ARCHITECTURE_BASELINE_V0.1.md` (Experimental / Temporary / Support First MVP);
  - Architecture Freeze v1.0 подтверждён как **ACTIVE** с явной областью: Governance Layer; Architecture Baseline v0.1; фундаментальные допущения MVP (B-001–B-005);
  - Freeze не запрещает реализацию MVP, исправление ошибок, развитие Orchestrator / Analyzer / Local Bridge / UI в пределах Baseline, Observation и сбор Evidence;
  - изменение замороженной архитектуры — только через Governance Pipeline и Action Gate пользователя;
  - открыт журнал `research/evidence/MVP-001-EVIDENCE.md` как стартовый журнал наблюдений (пустой шаблон записи не является Evidence принятия архитектуры).
- **Не решает:** изменение канона `PIPELINE.md`; принятие Validation как постоянной стадии; превращение Baseline в объективную модель AI POS; изменение Конституции.
- **Human Decision (кратко):** Accepted — временный/экспериментальный Baseline для First MVP; Freeze ACTIVE с областью выше; Validation не в каноне PIPELINE; постоянная архитектура из временных элементов Baseline без отдельного решения не следует.
- **Связанные документы:** `docs/architecture/ARCHITECTURE_BASELINE_V0.1.md`, `Governance/ADR/ADR-0002-architecture-freeze-v1.0.md`, `research/evidence/MVP-001-EVIDENCE.md`

---

## D-2026-07-27-04 — Layered Knowledge Principle (Accepted)

- **Дата:** 2026-07-27  
- **Статус:** Accepted  
- **Pipeline:** … → Action Gate → Accepted  
- **Решение:** в Конституцию добавлен принцип **11. Layered Knowledge Principle**: новые знания сначала изолируются и не влияют на действующую систему до завершения принятия через существующий Governance Pipeline; любая будущая подсистема обучения специалистов обязана использовать тот же Pipeline и не создавать собственный Action Gate.  
- **Не затрагивает:** Architecture Freeze v1.0 (ADR-0002); состав и статус остальных принципов 1–10; код, Orchestrator, Analyzer, Local Bridge, UI.  
- **Связанные документы:** `Governance/CONSTITUTION.md` (принцип 11), `Governance/PIPELINE.md`

---

## D-2026-07-29-01 — Состав главного экрана AI POS

- **Дата:** 2026-07-29  
- **Статус:** Accepted  
- **Action Gate:** не требуется — продуктовое решение в пределах Architecture Baseline v0.1; границы Orchestrator / Stage Engine / Analyzer и статус Health не затрагиваются.  
- **Решение:** На главном экране AI POS отображаются только реальные проекты пользователя. Явно обозначенный пример доступен исключительно при пустом списке проектов и не становится текущим проектом.  
- **Причина:** Главным объектом системы является проект пользователя (принцип 10), а система существует ради его целей (принцип 8). Главный экран, показывающий вымышленные проекты вместо реальных, вводит пользователя в заблуждение на первом же экране.  
- **Не решает:** состав полей карточки проекта сверх имеющихся в модели; шкалу стадий в интерфейсе (остаётся за Observation #1 и #4); ширину контента главного экрана; отдельную UX-проработку экрана «Текущая задача» и компактность мастера создания проекта.  
- **Связанные документы:** `index.html`, `Governance/ARCHITECTURAL_OBSERVATIONS.md` (#4), `docs/architecture/ARCHITECTURE_BASELINE_V0.1.md`
