# AI POS — Project Stage Engine

**Статус:** архитектурный документ; MVP реализован, полная модель — целевая архитектура  
**Дата:** 2026-07-26  
**Область:** механизм определения стадии проекта и следующего логичного шага  
**Вне области:** переписывание Intake, Discovery, Workflow State, Project Health, Delivery; планировщик задач  

**Реализация (факт):**  
- MVP: `tools/project_stage_engine.py` → `.ai-pos/project_stage.json`  
- MVP-стадии: `IDEA | INTAKE | DISCOVERY | PLANNING | EXECUTION` (маркеры файлов + substantive-check; EXECUTION при runtime-сигнале)  
- Полная модель стадий, GitHub evidence-адаптер, Stage History и каскад правил в этом документе остаются **целевой архитектурой**, не утверждением о полноте текущего кода  

---

## Внутренняя проверка перед фиксацией

| # | Вопрос | Результат |
|---|---|---|
| 1 | Работает ли модель без Git / GitHub? | **Да.** Стадии опираются на Intake, артефакты, задачи, Review, Delivery. Для программных проектов GitHub — сильный опциональный источник `system-confirmed` доказательств через `GitHubStageEvidenceAdapter`, но не назначает стадию и не обязателен. |
| 2 | Работает ли для PowerPoint, Word, Excel, исследования? | **Да.** Те же стадии; меняются только type-specific признаки артефактов и delivery. |
| 3 | Не дублирует ли Project Health? | **Нет.** Stage = «на каком этапе»; Health = «насколько состояние здорово». Красный Health возможен на любой стадии. |
| 4 | Объяснима ли стадия простыми словами? | **Да.** Каждая стадия имеет `stage_label` и короткое объяснение для UI. |
| 5 | Может ли исполняющий ИИ самовольно назначить стадию? | **Нет.** Стадию считает движок по фактам; AI-inferred не определяет стадию единолично; ручной override только за человеком. |
| 6 | Сохраняется ли история переходов? | **Да.** Stage History как отдельный класс Records, без удаления предыдущих переходов. |

---

## 1. Назначение

### Зачем отдельный Project Stage Engine

AI POS должна за секунды отвечать:

> На каком этапе сейчас проект и что логично делать дальше?

Без отдельного модуля стадия либо «назначается словами», либо путается с здоровьем, прогрессом и статусом задачи. Тогда разные типы проектов невозможно сравнивать, а следующий шаг становится субъективным.

Stage Engine — **детерминированный классификатор этапа жизненного цикла** на основе фактов, уже существующих в системе.

### Чем Stage отличается от соседних понятий

| Понятие | Вопрос | Пример |
|---|---|---|
| **Project Stage** | На каком этапе жизненного цикла мы? | «Проверка» |
| **Workflow State** | Какая задача/модуль/чек-лист активны сейчас? | Задача «доделать слайды 3–5» |
| **Project Health** | Насколько состояние в порядке? | «Требует внимания» |
| **Status** (проекта/модуля/задачи) | Локальная рабочая метка | «В работе», «Пауза» |
| **Progress** | Насколько продвинулись внутри этапа/задач | 3 из 7 задач приняты — *вспомогательный сигнал*, не стадия |

Stage **не заменяет** Workflow State и **не оценивает** Health.

### Почему стадия по фактам, а не только по словам

Слова пользователя важны, но:

- легко назвать проект «почти готовым» без артефакта;
- исполняющий ИИ может сдвинуть формулировку под удобный этап;
- после delivery часто начинается новая работа, а ярлык «готово» устаревает.

Поэтому Stage Engine использует **доказательства** (артефакты, review, delivery, intake).  
Слова пользователя — вход с уровнем `user-confirmed`, но не единственный источник.

---

## 2. Универсальная модель стадий

### Решение по составу

Базовый набор из запроса сохранён. Для ясности:

- **IDEA** оставляем как стадию *до* формального проекта (ещё нет якоря/intake).  
- **DISCOVERY** не сливаем с INTAKE: Intake = «что заводим», Discovery = «что реально нашли».  
- Переименований для MVP не требуется.  
- Не добавляем стадий вроде «Testing» / «Design» — они покрываются EXECUTION/REVIEW и workstreams.

Если команда захочет упростить MVP сильнее: допустимо объединить **IDEA → INTAKE** как один входной этап с подстатусом. Рекомендация архитектора: **оставить IDEA отдельно**, чтобы пустая идея не выглядела как уже подключённый проект.

### Стадии

#### 1. IDEA

| | |
|---|---|
| **Смысл** | Есть намерение, ещё нет оформленного проекта. |
| **Обязательные признаки** | Есть идея/цель в черновике **или** пользователь явно начал «новый проект»; нет подтверждённого Intake (тип + якоря). |
| **Дополнительные** | Заметки, ссылки-идеи, отсутствие рабочих артефактов. |
| **Исключающие** | Подтверждены тип проекта и якорные артефакты; есть frozen workspace. |
| **Типичные действия** | Сформулировать цель, выбрать тип, указать материалы. |
| **Возможный следующий** | INTAKE |

#### 2. INTAKE

| | |
|---|---|
| **Смысл** | Проект заводится: тип, имя, якоря, инструменты, план передачи. |
| **Обязательные признаки** | Идёт/не завершён Intake; тип или якоря ещё не полностью confirmed. |
| **Дополнительные** | Выбраны work tools; черновик delivery intent. |
| **Исключающие** | Intake завершён (тип confirmed + якоря заданы) и система уже может опираться на факты. |
| **Типичные действия** | Подтвердить тип, указать файл/папку, способ сдачи. |
| **Возможный следующий** | DISCOVERY |

#### 3. DISCOVERY

| | |
|---|---|
| **Смысл** | Система и пользователь выясняют, что реально существует. |
| **Обязательные признаки** | Intake достаточно завершён; идёт первичный сбор фактов **или** обязательные факты ещё `unknown`/не подтверждены; устойчивого плана задач ещё нет. |
| **Дополнительные** | Snapshot с provenance; кандидаты имени/структуры. |
| **Исключающие** | Есть confirmed понимание состава + хотя бы одна осмысленная текущая задача/план работ; либо проект уже в EXECUTION+ с историей review. |
| **Типичные действия** | Просмотреть найденное, подтвердить спорные поля, зафиксировать модули. |
| **Возможный следующий** | PLANNING (или EXECUTION, если план уже был и артефакты ясны) |

#### 4. PLANNING

| | |
|---|---|
| **Смысл** | Определяем, *что* делать: модули, задачи, правила, критерии. |
| **Обязательные признаки** | Состав проекта понятен; нет активной исполнения-сессии **или** нет задачи, готовой к исполнению; пользователь/система формирует план. |
| **Дополнительные** | Правила заполнены; scope черновики; этапные цели. |
| **Исключающие** | Есть активная задача в исполнении с gate/работой; или уже устойчивый цикл review/delivery. |
| **Типичные действия** | Добавить модуль/задачу, уточнить «можно/нельзя», критерии приёмки. |
| **Возможный следующий** | EXECUTION |

#### 5. EXECUTION

| | |
|---|---|
| **Смысл** | Идёт создание или изменение результата. |
| **Обязательные признаки** | Есть активная текущая задача; работа направлена на изменение артефактов; review текущей задачи ещё не `accepted` (или после accept сразу взята новая задача). |
| **Дополнительные** | Action Gate подтверждён; есть свежие изменения артефактов; незавершённые подзадачи. |
| **Исключающие** | Все активные направления ждут только проверки/приёмки без новой работы; или проект сдан и нет новых задач (см. DELIVERED/MAINTENANCE). |
| **Типичные действия** | Выполнить задачу в инструменте, скопировать задание, внести правки. |
| **Возможный следующий** | REVIEW |

#### 6. REVIEW

| | |
|---|---|
| **Смысл** | Результат есть, нужно проверить и принять/вернуть. |
| **Обязательные признаки** | По текущей доминирующей работе: есть что проверять (изменения/заявленный результат) **и** review ∈ {`unchecked`, `notes`} при ожидании приёмки; либо явный режим проверки. |
| **Дополнительные** | Чек-лист частично заполнен; замечания; scope_check unknown/fail. |
| **Исключающие** | Review текущей ключевой задачи `accepted` и нет другого blocking review; чистый planning без артефактного результата. |
| **Типичные действия** | Пройти чек-лист, принять или вернуть на доработку. |
| **Возможный следующий** | EXECUTION (доработка) / DELIVERY_PREPARATION / PLANNING (следующий блок) |

#### 7. DELIVERY_PREPARATION

| | |
|---|---|
| **Смысл** | Основная работа принята настолько, что готовим передачу/публикацию. |
| **Обязательные признаки** | Delivery plan задан; ключевой результат accepted (или accepted risk на сдачу); статус delivery ∈ {`planned`, `ready_to_deliver`}; ещё нет достоверного `delivered`/`published`. |
| **Дополнительные** | Экспорт PDF, сбор handoff, проверка ссылки, финальное имя файла. |
| **Исключающие** | Delivery уже `delivered`/`published` с evidence; или ключевой результат не принят и сдавать рано. |
| **Типичные действия** | Собрать пакет, экспортировать, проверить адрес/получателя. |
| **Возможный следующий** | DELIVERED |

#### 8. DELIVERED

| | |
|---|---|
| **Смысл** | Результат передан или опубликован. |
| **Обязательные признаки** | Delivery status ∈ {`delivered`, `published`} **и** есть evidence **или** user-confirmed факт передачи. |
| **Дополнительные** | Handoff packet; публичная ссылка; отметка «отправлено заказчику». |
| **Исключающие** | Появилась новая активная задача на развитие/исправление → переход в MAINTENANCE или EXECUTION (см. правила). |
| **Типичные действия** | Зафиксировать передачу, сообщить получателю, решить «архив или поддержка». |
| **Возможный следующий** | MAINTENANCE / ARCHIVED / EXECUTION (новый цикл) |

#### 9. MAINTENANCE

| | |
|---|---|
| **Смысл** | После сдачи идёт сопровождение, правки, обновления. |
| **Обязательные признаки** | Был факт DELIVERED (в истории) **и** есть новая активная задача / изменения после delivery. |
| **Дополнительные** | Hotfix, ECP, мелкие обновления контента. |
| **Исключающие** | Пользователь явно архивировал; или это первая сдача без предшествующего delivery. |
| **Типичные действия** | Точечные задачи, повторная проверка, повторная частичная доставка. |
| **Возможный следующий** | REVIEW / DELIVERY_PREPARATION / ARCHIVED |

#### 10. ARCHIVED

| | |
|---|---|
| **Смысл** | Проект сознательно закрыт для активной работы. |
| **Обязательные признаки** | User-confirmed архивация **или** политика «закрыт после delivery без активности» с подтверждением. |
| **Дополнительные** | Нет активных задач; delivery закрыт. |
| **Исключающие** | Есть активная задача или пользователь снял архив. |
| **Типичные действия** | Просмотр, handoff, разархивирование. |
| **Возможный следующий** | MAINTENANCE / EXECUTION (если открыли снова) |

---

## 3. Источники фактов

| Источник | Что даёт Stage Engine | Уровень доверия |
|---|---|---|
| Project Intake | Тип, якоря, завершённость заведения | `user-confirmed` + частично `system-confirmed` (полнота полей) |
| Discovery / Snapshot | Существование артефактов, freshness, unknown | `system-confirmed` (наличие/mtime); кандидаты типа — `AI-inferred`/`system` heuristics |
| Artifacts registry | Что считается проектом | `user-confirmed` якоря + `system-confirmed` existence |
| Workflow State | Этап работы в AI POS, модули | `user-confirmed` / `system-confirmed` (наличие записей) |
| Current Task | Активная задача, цель, состояние | `user-confirmed` |
| Action Gate | Была ли подготовка к передаче задачи ИИ | `user-confirmed` + `system-confirmed` timestamp |
| Review Records | unchecked / notes / accepted | `user-confirmed` (accept) + `system-confirmed` (факт статусов) |
| Delivery Records | plan / ready / delivered / evidence | `user-confirmed` и/или `system-confirmed` evidence |
| Project Timeline / activity | Давность изменений | `system-confirmed` |
| **GitHub** (software, через адаптер ниже) | Commits, PR, Issues, CI, releases, Pages… | в основном `system-confirmed`; выводы из текстов — не выше `AI-inferred` |
| Пользовательские подтверждения | Override стадии, архив, «сдано» | `user-confirmed` |
| AI-inferred подсказки | «Похоже на этап проверки» | `AI-inferred` — **никогда не единственное основание стадии** |

**Правило:** итоговая стадия требует минимум одного `system-confirmed` или `user-confirmed` доказательства из минимального набора стадии.  
`AI-inferred` может только предложить `PROVISIONAL` гипотезу при нехватке фактов.

### 3.1. GitHubStageEvidenceAdapter

Дополнение для **программных проектов** (`web_app`, `node`, `python` и др. software-типов).

GitHub используется как **один из основных источников системно подтверждённых фактов**, когда:

- в Intake/Discovery подтверждён GitHub remote / owner-repo;
- доступны `gh` или GitHub API (иначе поля адаптера = `unavailable`, стадия считается без них).

Адаптер **не назначает стадию**. Он возвращает набор `evidence[]` с кодами и уровнем доверия; каскад Stage Engine (раздел 4) решает сам.

Связь с существующей архитектурой:

- Discovery / `CodeProjectAdapter` / GitHubAnalyzer — факт «репозиторий связан и доступен»;
- `GitHubStageEvidenceAdapter` — узкий поставщик stage-evidence поверх тех же интеграций;
- без GitHub универсальная модель стадий **продолжает работать** (офис, дизайн, research, локальный код без remote).

#### Жёсткие ограничения

| Правило | Следствие |
|---|---|
| GitHub даёт доказательства, не стадию | Нет прямого `stage = f(github)` |
| Нет активности ≠ завершение / ARCHIVED | Тишина только усиливает timeline/Health, не закрывает проект |
| Закрытый Issue ≠ принятие результата в AI POS | Не подменяет Review `accepted` |
| Commit message недостаточное доказательство | Текст коммита ≤ `AI-inferred`; факт commit/date = `system-confirmed` |
| Решение пользователя приоритетно для accept/completion | User Review / Delivery / Archive важнее эвристик GitHub |
| Работа без GitHub обязательна | Адаптер optional; отсутствие = пустой evidence pack |

#### Что читает адаптер

| Область | Примеры фактов | Trust |
|---|---|---|
| Commits и активность | дата последнего commit, частота, авторы | `system-confirmed` (метаданные); смысл сообщения — не trust для стадии |
| Branches | default branch, feature branches, stale branches | `system-confirmed` |
| Issues и milestones | open/closed counts, milestone due/open | `system-confirmed` по состоянию объектов; «готово» по закрытию issue — **не** user accept |
| Pull Requests и review | open/merged/draft PR; requested/approved/changes-requested | `system-confirmed` для состояния PR; GitHub review ≠ AI POS Review accept |
| CI/CD checks | pending / success / failure на PR или commit | `system-confirmed` |
| Tags и releases | наличие release, draft/published, дата | `system-confirmed` |
| GitHub Pages / deployments | Pages status, deployment environments, URL | `system-confirmed` при API; иначе `unknown` |
| README, ROADMAP, проектные docs | факт наличия/mtime файлов в repo | `system-confirmed` наличие; содержание roadmap — только эвристика (`AI-inferred`) |

#### Признаки GitHub → поддержка стадий

Ниже — **усиливающие** признаки. Они повышают уверенность или участвуют в evidence, но не закрывают стадию в одиночку, если AI POS требует user-confirmed accept/delivery.

##### PLANNING

| Признак GitHub | Как использовать |
|---|---|
| Есть ROADMAP.md / docs/plan / milestone без merged PR по нему | Поддержка PLANNING |
| Open Issues с метками `enhancement`/`plan`, мало недавних commits по коду | Слабая поддержка PLANNING |
| Только README/инициализация репо, нет feature PR | Совместимо с PLANNING или DISCOVERY |
| **Недостаточно:** формулировки в commit «planning done» | Игнорировать как назначение стадии |

##### EXECUTION

| Признак GitHub | Как использовать |
|---|---|
| Недавние commits на рабочих ветках | Сильная поддержка EXECUTION |
| Open / draft / non-merged Pull Requests | Сильная поддержка EXECUTION |
| Open Issues в работе + связанный branch/PR | Поддержка EXECUTION |
| CI running / pending на активном PR | Поддержка EXECUTION (работа идёт) |
| **Недостаточно:** один старый commit без задачи в AI POS | Не переводить в EXECUTION без Workflow/active task при конфликте |

##### REVIEW

| Признак GitHub | Как использовать |
|---|---|
| PR в состоянии review: `review_requested`, `changes_requested`, `approved` но не merged | Сильная поддержка REVIEW (code review) |
| CI failed на PR, который ещё не закрыт | Поддержка REVIEW / возврат к доработке (вместе с EXECUTION — CONFLICTED/PROVISIONAL) |
| CI success + PR approved, ожидает merge | Поддержка REVIEW или DELIVERY_PREPARATION (см. приоритет каскада + AI POS review) |
| **Не равна стадии REVIEW в AI POS:** закрытие Issue | Только evidence «issue closed», не `review.accepted` |
| **Недостаточно:** commit «ready for review» | Текст = `AI-inferred` |

Важно: GitHub PR review подтверждает *кодовый* review.  
Принятие результата в AI POS по-прежнему требует Review Records пользователя, если политика задачи так задана.

##### DELIVERY_PREPARATION

| Признак GitHub | Как использовать |
|---|---|
| PR approved + CI green, ещё не merged | Поддержка DELIVERY_PREPARATION |
| Draft Release создан | Сильная поддержка DELIVERY_PREPARATION |
| Готовится deployment / Pages build in progress | Поддержка DELIVERY_PREPARATION |
| Milestone почти закрыт, остались release tasks | Слабая поддержка |
| **Недостаточно:** tag без published release и без user delivery plan | Не объявлять подготовку сдачи без Delivery plan / key accept в AI POS при CONFLICTED |

##### DELIVERED

| Признак GitHub | Как использовать |
|---|---|
| Published Release (не draft) | Сильное `system-confirmed` evidence delivery |
| GitHub Pages = built/published + URL | Сильное evidence для web delivery |
| Deployment environment `success` (production) | Сильное evidence |
| Merged PR в default + release notes опубликованы | Поддержка DELIVERED |
| **Недостаточно одних этих фактов для закрытия без пользователя, если:** в AI POS нет Delivery Records / user не подтвердил сдачу, а проект смешанный | Ставить evidence; `confidence` может быть PROVISIONAL; user completion имеет приоритет |
| Closed Issue «ship it» | **Не** считать DELIVERED |

Рекомендуемая связка: GitHub release/Pages = system evidence → AI POS Delivery status может стать `delivered`/`published` после политики «принять evidence» или явного user confirm (открытое решение в §15).

##### MAINTENANCE

| Признак GitHub | Как использовать |
|---|---|
| В истории уже был Release/Pages success **и** после даты release снова есть commits/PR | Сильная поддержка MAINTENANCE |
| Issues с метками `bug`/`hotfix` после release | Поддержка MAINTENANCE |
| Patch tags (`v1.0.1`) после major release | Поддержка MAINTENANCE |
| **Не делать:** «давно нет commits» → MAINTENANCE или ARCHIVED | Тишина ≠ сопровождение и ≠ архив |

#### Приоритет при конфликте с AI POS

```text
1. User Review accept / reject / archive / explicit delivery confirm
2. AI POS Delivery Records + локальные артефакты
3. GitHub system objects (release published, Pages, PR state, CI)
4. GitHub counts / milestones
5. Толкование текстов (commit/issue/README) = AI-inferred only
```

Если GitHub говорит «released», а пользователь в AI POS не принял результат и открыл замечания → стадия ближе к REVIEW/EXECUTION; release уходит в `conflicting_evidence` или workstream «production deploy».

#### Недоступность GitHub

```text
github_evidence.status = unavailable | unauthorized | not_applicable
```

- `not_applicable` — не software / нет remote;  
- `unavailable` — нет сети/API;  
- `unauthorized` — private repo без токена.

Stage Engine в этих случаях работает как универсальная модель без штрафного ARCHIVED/DELIVERED.

#### Выход адаптера (логически)

```text
GitHubStageEvidencePack
├── status                  // ok | unavailable | unauthorized | not_applicable
├── repo                    // owner/name если известно
├── fetched_at
├── signals[]
│   ├── code                // e.g. GH_PR_OPEN, GH_RELEASE_PUBLISHED
│   ├── supports_stages[]   // e.g. ["EXECUTION"]
│   ├── trust               // system-confirmed | AI-inferred
│   ├── summary             // коротко для UI «Почему так»
│   └── raw_ref             // id PR/release/… для Records
└── activity
    ├── last_commit_at
    └── note                // «отсутствие активности не закрывает проект»
```

---

## 4. Правила автоматического определения

### Принцип

Детерминированный **каскад от поздних стадий к ранним** (сначала проверяем «уже сдан/в архиве?», затем откатываемся к более ранним).  
Так частично доставленный проект с новой работой не застревает навсегда в DELIVERED.

Не использовать процент готовности как основной механизм.  
Допустимы счётчики задач только как *вспомогательные* признаки внутри PLANNING/EXECUTION.

### Приоритет фактов (высокий → низкий)

1. Явный ARCHIVED (user-confirmed)  
2. Delivery evidence + история DELIVERED (включая user-confirmed; GitHub release/Pages — сильный system evidence, см. §3.1)  
3. Review состояние активной/blocking работы в AI POS (GitHub PR review — поддержка, не замена)  
4. Наличие активной задачи и признаки исполнения (+ GitHub open PR/commits как усиление)  
5. Завершённость Intake / наличие якорей  
6. Snapshot existence / unknown  
7. Словесный статус пользователя  
8. AI-inferred (в т.ч. толкование commit/issue текста)  

### Порядок проверки (псевдологика)

```text
1. Если user-confirmed ARCHIVED и нет активной задачи → ARCHIVED
2. Если был DELIVERED в истории:
   2a. Если есть активная задача / изменения после delivery → MAINTENANCE
       (или EXECUTION, если maintenance ещё не «режим сопровождения» — см. ниже)
   2b. Иначе → DELIVERED
3. Если delivery готовится и ключевой accepted → DELIVERY_PREPARATION
4. Если доминирует ожидание приёмки (review unchecked/notes + есть результат) → REVIEW
5. Если есть активная задача на изменение → EXECUTION
6. Если состав ясен, но нет задачи к исполнению → PLANNING
7. Если intake ok, но факты/якоря сырые → DISCOVERY
8. Если intake не завершён → INTAKE
9. Иначе → IDEA
10. Если доказательств недостаточно → confidence_state=UNKNOWN, stage=лучшая гипотеза или null
```

Уточнение к 2a:  
- если после сдачи задача похожа на продолжение продукта → `MAINTENANCE`;  
- `EXECUTION` как global допустим, если delivery был частичным и основной продукт ещё не считался сданным (см. конфликты).

### Минимальный набор доказательств по стадиям

| Стадия | Минимум |
|---|---|
| IDEA | нет confirmed intake |
| INTAKE | начат проект, не закрыт intake |
| DISCOVERY | intake ok + (нет плана задач или высокий unknown по якорям) |
| PLANNING | якоря есть + нет active executable task |
| EXECUTION | active task + цель на изменение |
| REVIEW | active/blocking review не accepted + есть проверяемый результат |
| DELIVERY_PREPARATION | delivery plan + key accepted + not delivered |
| DELIVERED | delivered/published + evidence/confirm |
| MAINTENANCE | history has DELIVERED + new work |
| ARCHIVED | archive confirm |

### Условия перехода вперёд

Переход считается обоснованным, когда выполнены обязательные признаки следующей стадии и сняты исключающие текущей.  
Движок пересчитывает; «прыжок» через стадию возможен (например INTAKE → EXECUTION), если факты это показывают — история фиксирует факт.

### Условия возврата

Возврат **нормален**, не ошибка:

- REVIEW → EXECUTION при `notes` / новой доработке;  
- DELIVERED → MAINTENANCE при новой задаче;  
- DELIVERY_PREPARATION → REVIEW/EXECUTION если accept отозван или артефакт изменился после accept;  
- ARCHIVED → MAINTENANCE/EXECUTION при разархивации.

### Частичная доставка

Если delivered только один workstream (например отправлена презентация, сайт ещё нет):

- `global_stage` не обязан быть DELIVERED;  
- workstream «презентация» = DELIVERED;  
- blocking/dominant могут быть EXECUTION/REVIEW на других потоках;  
- global выбирается по правилам раздела 6.

### Параллельные направления

Считать стадии workstreams отдельно; global — функцией от них (раздел 6).  
Не усреднять «процентом».

---

## 5. Конфликты и неоднозначность

### Состояния уверенности

| Состояние | Смысл |
|---|---|
| **CONFIRMED** | Факты согласованы; хватает system/user доказательств |
| **PROVISIONAL** | Лучшая гипотеза; есть пробелы или слабые признаки |
| **CONFLICTED** | Противоречивые признаки разных стадий/источников |
| **UNKNOWN** | Нельзя достоверно выбрать стадию |

### Поведение в ситуациях

| Ситуация | Поведение |
|---|---|
| Признаки нескольких стадий | Выбрать по каскаду приоритета; параллельные — в workstreams; `CONFLICTED`, если два равносильных global-кандидата |
| Пользователь говорит одно, артефакты другое | Взять артефакты/records как основу; слова — в `conflicting_evidence`; UI: «Похоже иначе…» |
| Доставка была, затем новая задача | Global → MAINTENANCE (или EXECUTION при частичной сдаче); DELIVERED остаётся в history/workstream |
| Review завершён только частично | Global не DELIVERY_PREPARATION, пока blocking workstream в REVIEW/EXECUTION; reviewed часть — свой workstream_stage |
| Давно не менялся | Stage **не** менять на ARCHIVED автоматически; максимум PROVISIONAL + сигнал Health ( Holidays/activity — зона Health) |
| Есть файлы, нет цели | DISCOVERY или INTAKE; не EXECUTION |
| Нельзя определить | `confidence_state=UNKNOWN`; показать «нужно уточнить»; next_step = подтвердить тип/якорь/задачу |

Исполняющий ИИ **не** может установить `CONFIRMED` override.

---

## 6. Составной проект

### Понятия

| Термин | Определение |
|---|---|
| **workstream_stage** | Стадия одного направления (дизайн / тексты / разработка / публикация) |
| **blocking_stage** | Самая ранняя стадия среди незакрытых обязательных workstreams, которая мешает общей сдаче |
| **dominant_stage** | Стадия направления, на котором сейчас активна работа пользователя (active task / focus) |
| **global_stage** | Стадия, показываемая как основная для проекта |

### Как считается global_stage

```text
1. Если все обязательные workstreams ARCHIVED → ARCHIVED
2. Если все обязательные DELIVERED (и нет активной новой работы) → DELIVERED
3. Если есть активный focus task → global ≈ dominant_stage
4. Иначе global ≈ blocking_stage
5. Если blocking сильно расходится с dominant → confidence_state=CONFLICTED,
   UI показывает dominant + пометку о blocker
```

### Что показать пользователю первым

1. **dominant_stage** (где он работает сейчас) — крупно;  
2. если `blocking_stage` раньше и мешает сдаче — строка «Что блокирует общий результат»;  
3. global используется для навигации/фильтров и совпадает с dominant, пока нет конфликта.

Пример:

- дизайн: DELIVERED  
- тексты: REVIEW  
- разработка: EXECUTION  
- публикация: DELIVERY_PREPARATION  

Focus = разработка → пользователю: **«Выполнение»** + «Общую сдачу блокирует проверка текстов».

---

## 7. Следующий логичный шаг

Результат Stage Engine всегда включает следствие стадии — **не** полный план бэклога.

| Поле | Смысл |
|---|---|
| текущая стадия | `stage` + label |
| почему | 1–3 evidence в человекочитаемом виде |
| что мешает дальше | `blockers[]` |
| следующий логичный шаг | одно действие |
| неуместные сейчас действия | короткий список stop-hints |

Примеры next_step по стадиям:

| Стадия | next_step (тип) |
|---|---|
| IDEA | Сформулировать цель и выбрать тип проекта |
| INTAKE | Завершить подключение: тип и основные материалы |
| DISCOVERY | Просмотреть найденное и подтвердить спорное |
| PLANNING | Определить текущую задачу |
| EXECUTION | Выполнить текущую задачу в выбранном инструменте |
| REVIEW | Проверить результат и принять или вернуть |
| DELIVERY_PREPARATION | Подготовить передачу по плану сдачи |
| DELIVERED | Зафиксировать сдачу или решить: поддержка / архив |
| MAINTENANCE | Взять задачу сопровождения или закрыть в архив |
| ARCHIVED | Открыть снова только при необходимости |

Неуместные действия (примеры):

- в REVIEW — начинать новую крупную функцию до accept/notes;  
- в INTAKE — копировать задание исполняющему ИИ как будто scope ясен;  
- в DELIVERED без новой задачи — снова «разрабатывать с нуля» без причины.

---

## 8. Контракт результата

### Структура

```text
ProjectStageResult
├── stage                    // enum id
├── stage_label              // человекочитаемо
├── confidence_state         // CONFIRMED | PROVISIONAL | CONFLICTED | UNKNOWN
├── evidence[]               // { code, text, trust, source }
├── conflicting_evidence[]
├── blockers[]               // { text, related_stage?, workstream_id? }
├── next_step                // { text, action_hint }
├── inappropriate_actions[]  // короткие stop-hints
├── detected_at
├── source_freshness         // { snapshot_at, state_at, stale: boolean }
├── workstreams[]            // { id, name, stage, stage_label, blocking: boolean }
├── global_stage
├── dominant_stage
├── blocking_stage
└── override                 // null | { stage, until?, reason, set_by: user }
```

### JSON-пример (иллюстрация, не код модуля)

```json
{
  "stage": "REVIEW",
  "stage_label": "Проверка",
  "global_stage": "REVIEW",
  "dominant_stage": "REVIEW",
  "blocking_stage": "REVIEW",
  "confidence_state": "CONFIRMED",
  "evidence": [
    {
      "code": "REVIEW_PENDING",
      "text": "По текущей задаче результат ещё не принят",
      "trust": "user-confirmed",
      "source": "review_records"
    },
    {
      "code": "ARTIFACTS_PRESENT",
      "text": "Основные материалы на месте",
      "trust": "system-confirmed",
      "source": "artifacts"
    }
  ],
  "conflicting_evidence": [],
  "blockers": [
    {
      "text": "Итог не подтверждён",
      "related_stage": "REVIEW"
    }
  ],
  "next_step": {
    "text": "Проверить результат и принять или вернуть его на доработку",
    "action_hint": "open_review"
  },
  "inappropriate_actions": [
    "Начинать новую крупную задачу до завершения проверки",
    "Считать проект сданным"
  ],
  "detected_at": "2026-07-26T00:20:00.000Z",
  "source_freshness": {
    "snapshot_at": "2026-07-26T00:19:40.000Z",
    "state_at": "2026-07-26T00:19:55.000Z",
    "stale": false
  },
  "workstreams": [
    {
      "id": "ws-main",
      "name": "Основной результат",
      "stage": "REVIEW",
      "stage_label": "Проверка",
      "blocking": true
    }
  ],
  "override": null
}
```

---

## 9. Обновление стадии

### Когда пересчитывать

| Событие | Пересчёт |
|---|---|
| Подключение проекта | Полный |
| После Discovery / новый snapshot | Полный |
| Изменение якорных артефактов (mtime/hash/наличие) | Полный |
| Смена активной задачи / модуля | Локальный + пересчёт dominant/global |
| Закрытие/принятие задачи | Полный |
| Изменение Review | Полный |
| Изменение Delivery | Полный |
| Gate confirmation | Локальный (обычно не меняет stage один) |
| Запрос пользователя «обновить» | Полный |
| Ручной override | Локальный (фиксация override) + пометка history |

### Полный vs локальный

- **Полный:** заново прогнать каскад по всем источникам и workstreams.  
- **Локальный:** обновить dominant/blockers/next_step при узком событии, если global-кандидаты не затрагиваются; при сомнении — полный.

Stage Engine **не** обязан пересчитываться на каждый keystroke; достаточно событий выше + TTL freshness (согласуется с Discovery cache).

---

## 10. История стадий

Стадия не перезаписывается молча.

### Stage History Record

Отдельный тип Records (рядом с Decision/Audit, но не дублируя Audit):

| Поле | Содержание |
|---|---|
| `id` | стабильный идентификатор |
| `from_stage` | предыдущая (nullable для первой) |
| `to_stage` | новая |
| `reason` | краткая причина |
| `evidence_refs` | ссылки на evidence/коды |
| `initiator` | `system` / `user` |
| `transition_kind` | `automatic` / `user_confirmed` / `override` |
| `confidence_state` | на момент перехода |
| `timestamp` | дата/время |
| `correlation_id` | связь с task/delivery при необходимости |

Отличие от Audit Log:

- Audit: «произошло событие X»;  
- Stage History: «жизненный этап сменился с A на B потому что…».

Удаление запрещено; исправление — новой записью / supersede только для ошибочного override по правилам Records.

---

## 11. Пользовательский интерфейс

### Первые 5 секунд

Пользователь видит:

1. **Название стадии** простыми словами («Проверка», «Выполнение», «Подготовка к сдаче»).  
2. **Короткое объяснение** — одно-два предложения.  
3. **Следующий шаг** — одна строка.  
4. **Блокер**, если есть — одна строка спокойным тоном.

Не показывать сразу: enum id, JSON, хэши, внутренние evidence codes.

### Пример

> Проект находится на стадии проверки.  
> Основные материалы готовы, но итог ещё не подтверждён.  
> Следующий шаг — проверить результат и принять или вернуть его на доработку.

### Тон

Как у Project Health UX: навигировать, не пугать.  
При CONFLICTED: «Есть противоречие — давайте уточним», а не «ошибка классификации».

Детали и доказательства — под «Почему так».

---

## 12. Ошибки классификации

### Как пользователь исправляет

1. Открывает «Почему так».  
2. Выбирает «Указать другую стадию».  
3. Указывает стадию + короткую причину.  
4. Система пишет Stage History (`override` / `user_confirmed`).

### Временное vs устойчивое

| Вид | Условие |
|---|---|
| **Временный override** | Срок `until` или до следующего полного пересчёта по сильному событию (delivery/review/accept) |
| **Устойчивое решение** | Пользователь подтвердил «запомнить для этого проекта» **и** нет новых противоречащих system-фактов высшего приоритета; либо Decision Log зафиксировал правило проекта |

Сильные факты (новый delivered evidence, archive, появление active task после delivery) могут снять временный override с записью в history.

### «Обучение» без автоизменения общих правил

- Сохранять локальные preference/overrides проекта.  
- Копить анонимные паттерны расхождений для будущей настройки type profiles — **только после отдельного решения команды**.  
- Запрещено автоматически менять глобальные правила стадий из одного исправления пользователя.

---

## 13. Критерии готовности модуля (MVP)

Архитектуру Project Stage Engine считаем готовой к MVP, если:

1. Зафиксирован конечный набор стадий и их обязательные/исключающие признаки.  
2. Есть детерминированный каскад определения без % readiness.  
3. Разведены Stage vs Health vs Workflow.  
4. Описаны trust levels; AI-inferred не назначает CONFIRMED стадию.  
5. Есть контракт `ProjectStageResult`.  
6. Поддержаны workstreams / global / dominant / blocking на уровне модели.  
7. Описаны CONFLICTED / PROVISIONAL / UNKNOWN.  
8. Есть Stage History как Records-тип.  
9. Модель работает без Git и для office/research примеров.  
10. UI-смысл стадии объясняется простыми словами.  
11. Ручной override не даёт исполняющему ИИ права самоназначения.  
12. Открытые решения команды вынесены отдельно (раздел 15).
13. Зафиксирована граница с `project_analyzer` (раздел 14 / `PROJECT_ANALYZER_AND_STAGE_BOUNDARY.md`).

---

## 14. Граница с project_analyzer

Stage Engine **не заменяет** `project_analyzer.py` и не требует его удаления.

Полное описание разделения и схемы взаимодействия:

→ [`PROJECT_ANALYZER_AND_STAGE_BOUNDARY.md`](./PROJECT_ANALYZER_AND_STAGE_BOUNDARY.md)

Кратко:

| | Stage Engine | project_analyzer |
|---|---|---|
| Истина о стадии | да → `project_stage.json` | нет; только читает и объясняет |
| Сводка / риски | нет | да → `project_analysis.json` |
| Блокировки | нет | нет |
| CONFIRMED-стадия от ИИ | запрещено единолично | запрещено назначать |

Порядок: сначала Engine (или свежий `project_stage.json`), затем analyzer.

---

## 15. Открытые решения

### 1) Оставлять ли IDEA отдельной стадией в MVP?

- **Варианты:** A) IDEA отдельно; B) объединить с INTAKE.  
- **Рекомендация:** A — IDEA отдельно.  
- **Риски:** A — чуть сложнее модель; B — «просто идея» выглядит как уже заведённый проект.

### 2) После первой сдачи новая работа: всегда MAINTENANCE или иногда EXECUTION?

- **Варианты:** A) всегда MAINTENANCE; B) MAINTENANCE только если delivery был полного продукта, иначе EXECUTION.  
- **Рекомендация:** B.  
- **Риски:** A — путает «ещё не сдали основное» с сопровождением; B — нужны чёткие признаки partial delivery.

### 3) Автоархивация по давности без пользователя?

- **Варианты:** A) никогда; B) предлагать; C) авто после N дней.  
- **Рекомендация:** A/B — никогда автоматически в ARCHIVED, только предложение.  
- **Риски:** C — потеря активного «тихого» проекта; A — больше ручных действий.

### 4) Нужны ли workstreams в самом первом MVP?

- **Варианты:** A) сразу; B) v1 только global_stage, workstreams позже.  
- **Рекомендация:** B для скорости MVP; заложить поля в контракт сразу.  
- **Риски:** B — смешанные проекты временно грубее; A — дольше до первого полезного экрана.

### 5) Временный override: снимать ли автоматически при Review accept / Delivery?

- **Варианты:** A) снимать на сильных событиях; B) держать до `until`/ручного снятия.  
- **Рекомендация:** A.  
- **Риски:** A — пользователь может раздражаться; B — стадия «залипнет» вопреки фактам.

### 6) Показывать ли dominant или global при конфликте?

- **Варианты:** A) dominant + строка blocker; B) всегда global=blocking.  
- **Рекомендация:** A (как в разделе 6).  
- **Риски:** A — два «главных» смысла на экране; B — пользователь «теряет» то, над чем работает.

### 7) Автоматически ли считать published GitHub Release / Pages как Delivery evidence в AI POS?

- **Варианты:** A) только как stage evidence, delivery status меняет человек; B) system может выставить `delivered`/`published` при release/Pages success; C) system предлагает, человек одним действием подтверждает.  
- **Рекомендация:** C.  
- **Риски:** A — лишние клики при очевидном релизе; B — ложная «сдача» при тестовом/превью окружении; C — баланс контроля и скорости.

### 8) Обязателен ли GitHub для software-проектов в Stage Engine?

- **Варианты:** A) обязателен для CONFIRMED стадий EXECUTION+; B) опционален всегда, локальных фактов достаточно.  
- **Рекомендация:** B — опционален; при наличии становится *основным* system-источником, но локальный git/FS + AI POS records достаточны.  
- **Риски:** A — ломает офлайн и проекты без remote; B — слабее картина без GitHub (приемлемо как PROVISIONAL).

---

**Конец документа.**  
Реализация не начинается до подтверждения открытых решений и включения модуля в план этапа.
