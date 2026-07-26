# HEALTH (Project Health — Governance status)

Статус: **Draft**  
Основа Draft: **Hypothesis C** (гибридная модель)  
Решение: `DECISION_LOG` D-2026-07-27-02; Workshop: `HEALTH_DECISION_WORKSHOP_2026-07-27.md`

Версия контура: Architecture Freeze v1.0  
Связь: ADR-0002, PIPELINE.md, ARCHITECTURAL_OBSERVATIONS.md

## 1. Положение в Freeze v1.0

Project Health как продуктовый модуль **не принят** как Candidate/Accepted реализация.

В Architecture Freeze v1.0 Health находится на стадии Governance Pipeline:

**Draft**

Смысл: выбрана основа модели (Hypothesis C); готовится спецификация контура «тонкий слой индикаторов/отчёта + интерпретация в Analyzer».  
Код и обязательные блокировки на основе Health **не канонизируются** этим документом на стадии Draft.  
Спецификация набора индикаторов в данный Draft **ещё не входит** (отдельный шаг Draft-содержания).

Отличие от соседних Accepted-контуров:

| Контур | Вопрос | Статус в Freeze v1.0 |
|---|---|---|
| Stage Engine | На каком этапе? | архитектурно описан; истина стадии не у Health |
| project_analyzer | Сводка и риски (мягко) | контур развития; не истина стадии |
| Project Health | Насколько состояние в порядке? | **Draft** (основа: Hypothesis C) |

## 2. Основа Draft: Hypothesis C

### Выбранная модель

**Hypothesis C — Health как гибридная модель**

Есть тонкий слой Health-индикаторов (или отчёта), а развёрнутая интерпретация и мягкие рекомендации остаются в Analyzer.  
Границы ответственности между индикаторным слоем и Analyzer подлежат фиксации в ходе дальнейшей проработки Draft (без проектирования индикаторов в этой редакции).

Не назначает стадию проекта и не заменяет Review / Action Gate.

### Зафиксированные на Observation альтернативы (не основа Draft)

Ниже — гипотезы, рассмотренные на Observation и **не** выбранные как основа текущего Draft (см. Decision Workshop и D-2026-07-27-02).

#### Hypothesis A — Health как самостоятельный Engine

Health — отдельный детерминированный Engine со своими индикаторами, отчётом и контрактом результата.  
Не назначает стадию проекта и не заменяет Review / Action Gate.

#### Hypothesis B — Health как часть Analyzer

Отдельный Health Engine не вводится; оценка «здоровья» формируется внутри аналитической сводки `project_analyzer` / `project_analysis.json`.  
Стадию по-прежнему назначает только Stage Engine.

## 3. Что запрещено на стадии Draft

- Считать Health источником истины для стадии.
- Считать Draft эквивалентом Candidate/Accepted или канонизировать код/блокировки Health.
- Автоматически переводить Draft в Accepted без Evidence → Candidate → Action Gate.
- Подменять основу Draft (Hypothesis C) без нового решения по pipeline / DECISION_LOG.
- Выдавать текущий `needs_attention` Analyzer за принятый контракт Project Health.

## 4. Следующий шаг по pipeline

Hypothesis C зафиксирована как основа Draft. Далее:

1. Проработать Draft-содержание: контракт тонкого индикаторного слоя / отчёта, non-goals, граница с Analyzer (без преждевременной полной реализации).  
2. Собрать Evidence на пилотном проекте.  
3. Оформить Candidate.  
4. Пройти Action Gate.  
5. Accepted — только после человека-оператора.
