# ORCHESTRATOR

Статус: Accepted  
Версия контура: Architecture Freeze v1.0  
Связь: ADR-0002, PIPELINE.md, PROJECT_STAGE_ENGINE (вне Governance), PROJECT_ANALYZER_AND_STAGE_BOUNDARY (вне Governance)

## 1. Назначение

Orchestrator — тонкий координатор обновления проектного insight.

Он **не** является источником истины о стадии, здоровье или правилах.  
Он только запускает компоненты в правильном порядке и передаёт уже вычисленные артефакты дальше (UI, Records, человек).

## 2. Утверждённая ответственность

### Делает

1. Принимает событие обновления (подключение проекта, rescan, закрытие задачи, Review, Delivery, запрос пользователя).
2. Запускает **Project Stage Engine** (или переиспользует свежий `project_stage.json` по TTL).
3. Затем запускает **project_analyzer** с уже определённой стадией.
4. Собирает ссылки на результаты:
   - `project_stage.json` — фактическая стадия;
   - `project_analysis.json` — аналитическая сводка.
5. При необходимости инициирует чтение Fact Sources / адаптеров **без** собственной классификации стадии.

### Не делает

- не выбирает и не переписывает `stage`;
- не выставляет `confidence_state = CONFIRMED`;
- не блокирует Action Gate / Accept;
- не подменяет Project Health и Review;
- не является исполняющим ИИ задачи пользователя.

## 3. Минимальный порядок вызова

```text
event
  → Orchestrator
      → Stage Engine  → project_stage.json
      → project_analyzer (читает stage) → project_analysis.json
  → потребители (UI / Health observation / человек)
```

Если `project_stage.json` отсутствует или устарел:

- Orchestrator обязан обновить Stage Engine **до** analyzer;
- analyzer не имеет права выдумать официальную стадию.

## 4. Входы и выходы

| Направление | Артефакт |
|---|---|
| Вход | project root, event type, опционально TTL/force refresh |
| Выход Engine | `project_stage.json` |
| Выход Analyzer | `project_analysis.json` |
| Выход Orchestrator | статус прогона, пути к файлам, ошибки компонентов |

## 5. Ошибки и деградация

| Ситуация | Поведение |
|---|---|
| Stage Engine недоступен | прогон incomplete; analyzer не назначает stage |
| Analyzer недоступен | stage всё равно действителен; analysis = missing |
| GitHub/адаптер недоступен | продолжать без него (не блокировать оркестрацию) |

## 6. Связь с Governance Pipeline

Изменения самого Orchestrator проходят канонический pipeline:

`Observation → Hypothesis → Draft → Evidence → Candidate → Action Gate → Accepted`

Текущая роль Orchestrator в Architecture Freeze v1.0 — **Accepted** как координатор, не как ядро истины.
