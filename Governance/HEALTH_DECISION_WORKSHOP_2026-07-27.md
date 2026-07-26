# Project Health — Decision Workshop

**Дата:** 2026-07-27  
**Статус документа:** Workshop record (не DECISION_LOG, не изменение HEALTH.md)  
**Основание:** только ранее выполненные исследования — Architecture Audit Project Health; сравнение Hypothesis A/B/C; методологически исправленный вывод Observation #4 (Конституция = нормативный источник; три предметных применения).  
**Ограничение:** новый анализ и новые гипотезы не вводятся.

---

## 1. Цель Workshop

Зафиксировать трассируемое архитектурное Recommendation по выбору Hypothesis для Project Health (A / B / C), опираясь исключительно на уже подтверждённые факты и принятые нормы Freeze v1.0, **без** записи решения в `DECISION_LOG` и **без** перевода `HEALTH.md` в Draft до явного подтверждения человека.

---

## 2. Исходные подтверждённые факты

| # | Факт | Источник |
|---|---|---|
| F1 | Project Health в Freeze v1.0 имеет статус Governance **Observation**; код и блокировки на Health не канонизируются. | `Governance/HEALTH.md` §1; ADR-0002 п.5; `Governance/PIPELINE.md` (таблица контура) |
| F2 | Одновременно допустимы Hypothesis **A**, **B**, **C**; ни одна не Accepted. | `Governance/HEALTH.md` §2 |
| F3 | Выход из Observation: выбрать Hypothesis → Draft спецификации индикаторов → Evidence → Candidate → Action Gate → Accepted. | `Governance/HEALTH.md` §4 |
| F4 | Перевод Health из Observation в Draft/Candidate/Accepted — значимое изменение при Freeze. | `Governance/CHANGE_PROTOCOL.md` §3 |
| F5 | DECISION_LOG D-2026-07-26-01 **не решает** выбор единственной Health Hypothesis. | `Governance/DECISION_LOG.md` D-01 |
| F6 | Продуктового Health Engine / UI Health / отдельного health-артефакта в коде нет. `/api/health` — liveness Bridge, не Project Health. | Architecture Audit Project Health |
| F7 | В Analyzer MVP есть `needs_attention`; это не объявлено как Project Health и не выбирает стадию. | Architecture Audit; `PROJECT_ANALYZER_AND_STAGE_BOUNDARY.md` §2.1 |
| F8 | Stage = этап; Analyzer = сводка/интерпретация; артефакты разделены (`project_stage.json` / `project_analysis.json`). | D-2026-07-26-02; Observation #1; Boundary; ADR-0002 п.3 |
| F9 | Внешний evidence ≠ Accept / завершение работы человеком. | Observation #2; ADR-0002 п.4; PIPELINE (Evidence ≠ Accepted) |
| F10 | Constitution Принцип 2: нормы и факты разделяются. | `Governance/CONSTITUTION.md` |
| F11 | Constitution Принцип 5: Orchestrator — диспетчер, не судья истины. | `Governance/CONSTITUTION.md`; `Governance/ORCHESTRATOR.md` §1 |
| F12 | Constitution Принцип 3: никто не проверяет сам себя (в т.ч. Analyzer, Health). | `Governance/CONSTITUTION.md` |
| F13 | Методология Observation #4 (исправленная): Конституция — **нормативный источник** паттерна «факты / интерпретация»; три независимых предметных применения: (1) Stage/Analyzer, (2) Evidence/Accept, (3) Project Health. | Исправленный вывод Observation #4 (workshop input) |
| F14 | Паттерн «факты отдельно — интерпретация отдельно» признан устойчивым (норма + три применения), не совпадением четырёх равноправных контекстов. | Тот же исправленный вывод |

---

## 3. Проверка каждой Hypothesis

### 3.1. Hypothesis A — Health как самостоятельный Engine

| Ось проверки | Результат проверки | Трассировка |
|---|---|---|
| Principle 2 (Constitution) | **Согласуется:** отдельный детерминированный отчёт/индикаторы отделяют факт здоровья от нарратива и от норм Gate. | CONSTITUTION П.2; HEALTH.md §2 A |
| Stage / Analyzer | **Согласуется с границей Stage:** A явно не назначает стадию. **Расширяет** runtime-контур: третий компонент/артефакт сверх принятой цепи Engine→Analyzer. | HEALTH.md §2 A; ORCHESTRATOR.md §3 (текущий порядок: Engine→Analyzer); Boundary §2–3 |
| Evidence / Accept | **Согласуется:** A не заменяет Review / Action Gate; health-факт ≠ Accept. | HEALTH.md §2 A; Observation #2; PIPELINE Action Gate |
| Observation #4 (испр.) | **Согласуется с паттерном:** выделяет фактологический слой здоровья как отдельное применение (3), по аналогии с отделением факта от интерпретации в применении (1). | F13–F14; применение (3) = Project Health |

### 3.2. Hypothesis B — Health как часть Analyzer

| Ось проверки | Результат проверки | Трассировка |
|---|---|---|
| Principle 2 (Constitution) | **Слабое согласование:** оценка здоровья помещается в аналитическую/эвристическую сводку; разделение «факт здоровья» vs «интерпретация» внутри одного артефакта не гарантировано контрактом. | CONSTITUTION П.2; HEALTH.md §2 B; Boundary: analysis — не истина стадии, эвристический слой |
| Stage / Analyzer | **Согласуется со Stage** (стадию не назначает). **Совмещает** Health с ролью Analyzer, уже определённой как объяснение/сводка, не как отдельная истина. | HEALTH.md §2 B; Boundary §2.1; D-02 |
| Evidence / Accept | **Согласуется на уровне запрета Accept:** Analyzer по Boundary не является Action Gate. Риск: health, растворённый в analysis, читается UI как «вторая картина» рядом со stage (известный риск Observation #1). | Boundary §2.1 «не блокирует… не Action Gate»; Observation #1 |
| Observation #4 (испр.) | **Напряжение с паттерном:** применение (3) строится на той же оси «факт / интерпретация», что и (1); B помещает здоровье в слой интерпретации применения (1), не выделяя фактологический слой здоровья. | F13–F14; HEALTH.md §2 B |

Дополнительно по Principle 3: совмещение «сводка» и «оценка здоровья» в одном компоненте **ослабляет** разделение предлагающего/оценивающего контура относительно П.3 (CONSTITUTION; перечень включает Analyzer и Health).

### 3.3. Hypothesis C — гибридная модель

| Ось проверки | Результат проверки | Трассировка |
|---|---|---|
| Principle 2 (Constitution) | **Согласуется:** тонкий слой индикаторов/отчёта (факт) отделён от развёрнутой интерпретации в Analyzer. | CONSTITUTION П.2; HEALTH.md §2 C |
| Stage / Analyzer | **Структурный прецедент применения (1):** факт (`project_stage.json`) + интерпретация (`project_analysis.json`). C воспроизводит ту же ось для здоровья: индикаторы ≠ нарратив Analyzer. Стадию не назначает. | D-02; Boundary §3; HEALTH.md §2 C; Observation #1 |
| Evidence / Accept | **Согласуется:** индикаторы/отчёт не заменяют Gate/Accept; интерпретация остаётся мягкой, как роль Analyzer. | HEALTH.md §2 C; Observation #2; Boundary §2.1 |
| Observation #4 (испр.) | **Прямое соответствие паттерну:** применение (3) получает ту же структуру, что применение (1), при нормативном источнике в Конституции. | F13–F14; HEALTH.md §2 C |

Ограничение формулировки C (факт документа): границы «уточняются при переходе Observation → дальнейшие стадии» — Draft обязан их зафиксировать (`HEALTH.md` §2 C, §4).

---

## 4. Сравнительная таблица

| Критерий | A | B | C | Опора |
|---|---|---|---|---|
| Отделение факта здоровья от интерпретации | Да (отдельный Engine) | Не гарантировано | Да (тонкий слой + Analyzer) | П.2; Observation #4 испр. |
| Сохранение границы Stage ≠ Health | Да | Да | Да | HEALTH.md; Stage Engine FAQ |
| Согласование с прецедентом Stage/Analyzer (факт + объяснение) | Аналог полного Engine-слоя | Health внутри explanation-слоя | Прямой аналог двухартефактной схемы | D-02; Boundary |
| Согласование с Evidence ≠ Accept | Да | Да (с риском UI-смешения) | Да | Observation #2 |
| Principle 3 (не проверяй сам себя) | Сильнее (отдельный контур) | Слабее (тот же Analyzer) | Сильнее на индикаторах | CONSTITUTION П.3 |
| Вписывание в текущий Orchestrator MVP (Engine→Analyzer) | Требует третьего шага/артефакта | Минимальное изменение цепи | Умеренное: thin health + Analyzer | ORCHESTRATOR.md §3 |
| Риск выдать текущий `needs_attention` за принятый Health | Ниже | Выше | Средний (если индикаторы не специфицированы) | Audit F6–F7; HEALTH.md запрет считать Observation Accepted |
| Зрелость границ в тексте Freeze | Высокая | Высокая | Требует уточнения в Draft | HEALTH.md §2 C |

---

## 5. Обоснование преимуществ и компромиссов

### Hypothesis A

- **Преимущество (проверяемо):** максимальное отделение фактологического контура здоровья от Analyzer и от Stage — согласуется с П.2, П.3 и запретом HEALTH.md «не назначает стадию / не заменяет Gate».  
- **Компромисс (проверяемо):** Accepted-порядок Orchestrator сегодня фиксирует Engine→Analyzer и два артефакта (`ORCHESTRATOR.md` §3–4); A вводит третий обязательный контур до прохождения полного pipeline на Health (ADR-0002: полный код Health out of Freeze до решения).

### Hypothesis B

- **Преимущество (проверяемо):** совпадает с минимальным инкрементом к уже реализованной цепи Engine→Analyzer и с наличием `needs_attention` в analysis MVP (Boundary §2.1; Audit F7).  
- **Компромисс (проверяемо):** помещает Health в эвристический слой, для которого Boundary явно отрицает статус истины стадии; по исправленному Observation #4 это **не** воспроизводит ось применения (1) для применения (3). Усиливает риск Observation #1 (две картины для пользователя) и ослабляет П.3.

### Hypothesis C

- **Преимущество (проверяемо):** воспроизводит уже Accepted прецедент применения (1) — отдельный фактологический слой + интерпретация Analyzer — для применения (3), при том же нормативном источнике (П.2; Observation #4 испр.). Сохраняет запреты A/B относительно Stage и Gate.  
- **Компромисс (проверяемо):** текст HEALTH.md §2 C оставляет границы «на уточнение»; без Draft-спеки индикаторов возможен срыв в B (только поля analysis) или разрастание в A (толстый Engine) — это ограничение документа, не отмена структурного соответствия паттерну.

---

## 6. Recommendation

### R1 — Нормативная рамка выбора

Выбор Hypothesis для Project Health обязан сохранять Constitution Принцип 2 и воспроизводить структуру, уже принятую для предметного применения (1) Stage/Analyzer, потому что исправленный Observation #4 устанавливает: Конституция — источник нормы; Project Health — третье применение той же оси, а не отдельная произвольная модель.

- Опора: CONSTITUTION П.2; Observation #4 (испр.); D-02; Boundary §3.

### R2 — Несоответствие B как полной модели Health

Hypothesis B **не** удовлетворяет R1: она размещает оценку здоровья внутри интерпретирующего слоя Analyzer и не выделяет фактологический слой здоровья, требуемый той же осью, что отделяет `project_stage.json` от `project_analysis.json`.

- Опора: HEALTH.md §2 B; Boundary §2.1–3; Observation #1; Observation #4 (испр.); CONSTITUTION П.2, П.3.

### R3 — Сопоставление A и C относительно прецедента Freeze

И A, и C согласуются с R1 на уровне отделения факта от интерпретации и с запретами Stage/Gate (HEALTH.md §2 A/C; Observation #2).

Различие, проверяемое по документам:

- **A** = отдельный полный Engine-контур (новый обязательный компонент относительно текущего `ORCHESTRATOR.md` §3).  
- **C** = тонкий индикаторный/отчётный слой + интерпретация в Analyzer — та же схема разделения ролей, что уже Accepted для Stage (факт) и Analyzer (объяснение) в D-02 / Boundary / ORCHESTRATOR.

### R4 — Workshop Recommendation (для подтверждения человеком)

**Architecture Recommendation Workshop:** рекомендовать человеку рассмотреть Hypothesis **C** (гибридная модель) как основу Draft Project Health, потому что:

1. Она единственная из A/B/C **явно** формулирует пару «индикаторы/отчёт + интерпретация Analyzer» в `HEALTH.md` §2 C;  
2. Эта пара **изоморфна** уже принятому разделению Stage/Analyzer (D-02; Boundary §3; Observation #1) — предметное применение (1) из Observation #4 (испр.);  
3. Она **согласуется** с Principle 2 и с Evidence≠Accept (не заменяет Gate) — применения нормативного источника и прецедента (2);  
4. Workshop **не рекомендует** Hypothesis B как полную модель Project Health (по R2);  
5. Hypothesis A **не объявляется запретной**, но **не рекомендуется как первый Draft-контур**, пока не доказана необходимость полного Engine сверх thin-слоя: текущий Accepted Orchestrator описывает два результата прогона (stage + analysis), а ADR-0002 удерживает полный код Health вне Freeze до прохождения pipeline; C допускает тонкий слой без немедленного приравнивания к полному A.

Проверяемые следствия при подтверждении человеком (вне объёма этого файла): Draft `HEALTH.md` должен зафиксировать контракт индикаторов, non-goals (не Stage, не Gate), границу с `project_analysis.json` / `needs_attention`, чтобы исключить срыв C→B.

### R5 — Что Workshop явно не делает

- Не записывает DECISION_LOG.  
- Не меняет статус `HEALTH.md`.  
- Не объявляет Hypothesis Accepted.  
- Не вводит Hypothesis D или иные новые модели.

---

Architecture Recommendation завершена.

Hypothesis не выбрана.

Ожидается архитектурное решение человека.

После явного подтверждения человека допускается:
1. запись решения в DECISION_LOG;
2. перевод HEALTH.md в Draft.
