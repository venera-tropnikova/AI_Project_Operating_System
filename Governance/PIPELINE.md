# Governance Pipeline

Статус: Accepted  
Версия контура: Architecture Freeze v1.0  
Связь: ADR-0002, CONSTITUTION.md

## Каноническая последовательность

Любое значимое архитектурное или управленческое изменение в AI POS проходит стадии:

```text
Observation
    → Hypothesis
        → Draft
            → Evidence
                → Candidate
                    → Action Gate
                        → Accepted
```

Это **канон Freeze v1.0**. Иные ярлыки статуса («готово», «вроде ок», «Draft навсегда») не заменяют стадий pipeline.

## Смысл стадий

| Стадия | Смысл | Кто двигает дальше |
|---|---|---|
| **Observation** | Заметили явление/риск/потребность; ещё нет выбранной гипотезы | человек / журнал наблюдений |
| **Hypothesis** | Есть конкурирующие или одна рабочая гипотеза решения | человек фиксирует выбор гипотезы |
| **Draft** | Черновик спецификации/документа/правила | автор-человек (+ ИИ как помощник) |
| **Evidence** | Собраны доказательства применимости (пилот, сверка, контрпример) | человек подтверждает достаточность evidence |
| **Candidate** | Кандидат на принятие; готов к проверке границ | подготовка к Action Gate |
| **Action Gate** | Обязательная проверка перед принятием (границы, риски, обратимость) | человек подтверждает gate |
| **Accepted** | Принято как действующая норма контура | только после Gate; фиксируется в ADR / DECISION_LOG |

## Правила

1. Нельзя перескочить сразу в Accepted без Action Gate.  
2. ИИ может помогать на Observation…Draft, но **не** завершает Action Gate и Accepted единолично.  
3. Несколько Hypothesis могут сосуществовать на Observation (пример: Health A/B/C).  
4. Rejected / Superseded не стирают историю: фиксируются новой записью.  
5. Architecture Freeze ограничивает *содержание* Accepted-контура, но не отменяет pipeline для будущих изменений.

## Примеры текущего контура

| Элемент | Стадия pipeline |
|---|---|
| Governance Pipeline (этот документ) | Accepted |
| Orchestrator (роль) | Accepted (в рамках Freeze) |
| Project Health | Draft (Hypothesis C); D-2026-07-27-02 |
| Architectural Observations #1–#3 | Observation (журнал) |
| Architecture Freeze v1.0 | Accepted (ADR-0002) |
