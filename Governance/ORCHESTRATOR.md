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

## 5. Режимы работы

Orchestrator всегда завершает прогон в одном из трёх режимов:  
`NORMAL` | `DIAGNOSTIC` | `BLOCKED`.

Режим выбирается по закрытому списку `reason_codes` (без оценочных формулировок).

### Правило выбора

```text
BLOCKED > DIAGNOSTIC > NORMAL
```

- есть хотя бы один BLOCKED-код → `BLOCKED`;
- иначе есть хотя бы один DIAGNOSTIC-код → `DIAGNOSTIC`;
- иначе → `NORMAL`.

### NORMAL

Все обязательные компоненты успешно завершены.  
Официальная стадия определена (`project_stage.json` валиден, поле `stage` задано).  
Обязательные артефакты текущего прогона доступны (включая валидный `project_analysis.json`).  
`reason_codes` пуст.

### DIAGNOSTIC

Оркестрация завершена, стадия определена, но есть неблокирующие проблемы текущего прогона.

Закрытый список DIAGNOSTIC-кодов (как в реализации):

| `reason_code` | Условие |
|---|---|
| `ANALYZER_FAILED` | Analyzer завершился с ошибкой |
| `ANALYSIS_JSON_MISSING` | после Analyzer нет `project_analysis.json` |
| `ANALYSIS_INVALID` | `project_analysis.json` невалиден / `valid=false` |
| `OPTIONAL_ADAPTER_UNAVAILABLE` | зарезервирован (MVP не активирует) |
| `STAGE_TTL_REUSED` | зарезервирован (MVP не активирует) |

Перед запуском Analyzer артефакт предыдущего `project_analysis.json` снимается, чтобы DIAGNOSTIC не опирался на результат прошлого успешного прогона.

### BLOCKED

Оркестрация прекращается; Analyzer не запускается (если стадия/корень уже невалидны).

Закрытый список BLOCKED-кодов (как в реализации):

| `reason_code` | Условие |
|---|---|
| `PROJECT_ROOT_INVALID` | невозможно определить корень проекта (путь отсутствует / не директория / не резолвится) |
| `STAGE_ENGINE_FAILED` | Stage Engine завершился ошибкой |
| `STAGE_JSON_MISSING` | `project_stage.json` не создан |
| `STAGE_JSON_INVALID` | `project_stage.json` не читается или не проходит обязательную проверку структуры (`stage` обязателен) |
| `REQUIRED_INPUT_JSON_MISSING` | зарезервирован под будущий обязательный входной JSON (MVP: вход — путь проекта) |

Запрещается использовать оценочные формулировки  
вроде «если система считает ситуацию критичной».

Потребители (в т.ч. Local Bridge) при `BLOCKED` не подставляют analysis предыдущего прогона в ответ текущего.

## 6. Ошибки и деградация

Согласовано с §5:

| Ситуация | Режим | Поведение |
|---|---|---|
| Stage Engine недоступен / ошибка | `BLOCKED` | Analyzer не запускается; стадию Analyzer не назначает |
| Analyzer недоступен / ошибка при валидной стадии | `DIAGNOSTIC` | stage остаётся действительным; analysis текущего прогона отсутствует или invalid |
| GitHub / необязательный адаптер недоступен | `DIAGNOSTIC` (код `OPTIONAL_ADAPTER_UNAVAILABLE`, когда будет активен) | оркестрацию не блокировать |

## 7. Связь с Governance Pipeline

Изменения самого Orchestrator (включая набор режимов, правило выбора и закрытые списки `reason_codes`) проходят канонический pipeline:

`Observation → Hypothesis → Draft → Evidence → Candidate → Action Gate → Accepted`

Текущая роль Orchestrator в Architecture Freeze v1.0 — **Accepted** как координатор, не как ядро истины.  
Режимы `NORMAL` / `DIAGNOSTIC` / `BLOCKED` входят в Accepted-контур Orchestrator и не заменяют стадии Governance Pipeline.
