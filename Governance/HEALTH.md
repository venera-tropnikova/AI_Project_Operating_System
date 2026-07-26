# HEALTH (Project Health — Governance status)

Статус: **Observation**  
(не Draft)

Версия контура: Architecture Freeze v1.0  
Связь: ADR-0002, PIPELINE.md, ARCHITECTURAL_OBSERVATIONS.md

## 1. Положение в Freeze v1.0

Project Health как продуктовый модуль **не принят** как Candidate/Accepted реализация.

В Architecture Freeze v1.0 Health фиксируется на стадии Governance Pipeline:

**Observation**

Смысл: наблюдаем потребность в модуле «здоровье проекта» и конкурирующие способы его ввести.  
Код и обязательные блокировки на основе Health **не канонизируются** этим документом.

Отличие от соседних Accepted-контуров:

| Контур | Вопрос | Статус в Freeze v1.0 |
|---|---|---|
| Stage Engine | На каком этапе? | архитектурно описан; истина стадии не у Health |
| project_analyzer | Сводка и риски (мягко) | контур развития; не истина стадии |
| Project Health | Насколько состояние в порядке? | **Observation** |

## 2. Три конкурирующие Hypothesis

Пока статус Observation, одновременно допустимы три гипотезы.  
Ни одна не является Accepted без прохождения pipeline.

### Hypothesis A — Health как самостоятельный Engine

Health — отдельный детерминированный Engine со своими индикаторами, отчётом и контрактом результата.  
Не назначает стадию проекта и не заменяет Review / Action Gate.

### Hypothesis B — Health как часть Analyzer

Отдельный Health Engine не вводится; оценка «здоровья» формируется внутри аналитической сводки `project_analyzer` / `project_analysis.json`.  
Стадию по-прежнему назначает только Stage Engine.

### Hypothesis C — Health как гибридная модель

Есть тонкий слой Health-индикаторов (или отчёта), а развёрнутая интерпретация и мягкие рекомендации остаются в Analyzer.  
Границы ответственности уточняются при переходе Observation → дальнейшие стадии pipeline.

## 3. Что запрещено, пока статус Observation

- Считать Health источником истины для стадии.
- Автоматически переводить Observation в Accepted без Evidence → Candidate → Action Gate.
- Утверждать одну Hypothesis A/B/C как единственную без решения по pipeline.

## 4. Следующий шаг по pipeline

Чтобы выйти из Observation:

1. Выбрать одну Hypothesis (или явную комбинацию) → Hypothesis (зафиксировать).  
2. Подготовить Draft спецификации индикаторов.  
3. Собрать Evidence на пилотном проекте.  
4. Оформить Candidate.  
5. Пройти Action Gate.  
6. Accepted — только после человека-оператора.
