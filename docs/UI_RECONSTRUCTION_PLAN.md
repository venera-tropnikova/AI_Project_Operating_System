# UI Reconstruction Plan — AI POS

| Поле | Значение |
|---|---|
| Document Type | UI reconstruction plan (факт + план переноса) |
| Status | Active working plan |
| Date | 2026-07-30 |
| Branch (clean UI) | `ui/split-index` @ `D:\AI_POS_UI_SPLIT` |
| Source WIP | `D:\AI_Project_Operating_System` `master` @ `96e0498` + dirty `index.html` |
| Canon | `Governance/CONSTITUTION.md` (приоритет при конфликте) |
| Related | ADR-0002 Freeze; Observations #5–#6; `Standards/DEVELOPMENT_STANDARD.md`; `Standards/REVIEW_STANDARD.md`; User First |

**Режим документа:** только фиксация аудита и порядка работ. Код этим файлом не изменяется.

---

## 1. Эталонная архитектура интерфейса и обязательные контракты

### 1.1. Продуктовый эталон (User First + Конституция)

- Главный объект — **проект** (принцип 10).
- Система существует ради целей пользователя (принцип 8); интерфейс должен быть понятен без терминала, JSON и служебных путей (User First).
- Решения объясняются понятным языком (принцип 9), без раскрытия всей внутренней кухни.
- Нормы и факты разделены (принцип 2): UI не подменяет Stage Engine / Analyzer / Gate.
- Запуск: идеально «двойной щелчок → AI POS»; Local Bridge обслуживает UI, но не становится предметом выбора пользователя.

### 1.2. Инженерные контракты UI ↔ система

| Контракт | Источник истины | Роль UI |
|---|---|---|
| Список проектов пользователя | `localStorage` (`ai-pos-projects-v1`) | Читать/показывать; локальные поля карточки (имя, идея, статус) |
| Файлы проекта / папка | Файловая система через Local Bridge | Не подменять путь искусственной записью в storage без действия пользователя (см. Observation #6) |
| Паспорт проекта | `.ai-pos/project_passport.json` via Bridge `/api/project-passport/*` | Клиент read/write; согласование с `project_id` |
| Стадия системы | Stage Engine → `project_stage.json` + `stage_model` via `/api/project-stage/read` | Отображать модель с Bridge; **не** держать собственный enum стадий |
| Карточка `project.stage` | localStorage (D-2026-07-26-04) | «Текущая работа» — локальное рабочее поле, не истина Stage Engine |
| Анализ | Analyzer / Orchestrator via Bridge | Показывать сводку; не назначать стадию |
| Идентичность проекта | `passport.project_id` ↔ `project.id` в списке | Один проект — один id; антидубли по id и нормализованному пути |

### 1.3. Целевая карта экранов (эталон из грязного UI + канон)

```text
[Boot — опционально] → Главная «Проекты» (таблица)
                         ↓ открытие строки
                    Project Chrome (верхняя оболочка)
                         ├── Обзор / Текущая задача / Правила / …
                         └── ← Проекты

Отдельно (ещё не в clean ветке):
  Подключить существующий (pick → loading → review)
  Создать новый (create-story + мастер + folder)
  Passport sync / stage track на обзоре
```

### 1.4. Обязательные правила переноса

1. Один коммит = одна законченная логическая UI-задача (`DEVELOPMENT_STANDARD`).
2. Backend/Bridge, уже в HEAD (`stage_model`, passport API), **не** включать повторно в UI-коммиты.
3. Не копировать целиком грязный `index.html`; переносить минимальный HTML/CSS/JS вручную.
4. Не подсаживать тестовые проекты и не писать в `localStorage` без действия пользователя.
5. Перед «значимым» UI-коммитом — предъявление результата (`REVIEW_STANDARD`); Observation #6 учитывать для сценариев с folder picker.

---

## 2. Что уже чисто перенесено и закоммичено

**Ветка:** `ui/split-index`
**Коммит:** `4851044` — `feat(projects): add projects home and local management`
**База:** `96e0498` (passport Bridge API уже в истории)

| ID | Содержание | Статус |
|---|---|---|
| **UI-01** | Главная «Проекты»: `#systemHome`, таблица `#pmTable`, empty state, поиск/фильтр/сортировка, меню строки, `loadProjects`/`saveProjects`, `findProjectRecord` для живых мутаций | **Committed** |

**Не входит в UI-01 (намеренно):** connect/create, Passport client, `project_id` antidupe, `stage_model`, create-story, history nav, ensureMoyDen, boot, Project Chrome.

---

## 3. Текущее незакоммиченное состояние Project Chrome

**Дерево:** `D:\AI_POS_UI_SPLIT`
**Относительно HEAD `4851044`:** dirty `index.html` (~+212 / −4)

| Элемент | Факт |
|---|---|
| HTML | `#projectChrome`, `#osBackToProjects`, `#osNavProjectName`, `#osNavProject` + разделы как в эталоне |
| CSS | `.project-chrome*`, `.project-section-nav*`, `.ai-pos-level-nav*` |
| JS | `syncProjectChrome`, `navIdForActiveTab`; правки `showPanel` / `setOsNavActive` / `openOsSection` / `openWorkspace` |
| History | **нет** `pushNavState` / browser history |
| Проверка | READY по аудиту: имя проекта, активный раздел, ← Проекты, повторное открытие, сохранность таблицы |
| Staging | **пусто** (не подготовлен) |
| Побочный шум | `tools/__pycache__/…` — не часть задачи |

**Следующий шаг по Chrome:** подготовить staging **только** `index.html` → коммит **UI-02** (после явного подтверждения).

---

## 4. Оставшиеся изменения основного `index.html` (группировка)

Источник: dirty `D:\AI_Project_Operating_System\index.html` vs HEAD `96e0498` (~+6385 / −1875, ~49 hunks). Backend passport/stage уже committed — ниже только **UI-остаток**.

| Группа | Условное имя | Содержание в dirty UI | Завершённость в источнике |
|---|---|---|---|
| A | Connect existing | pick → loading → review → confirm; notices/conflicts | COMPLETE (сценарий) |
| B | Identity / anti-dupe | `project_id`, normalize path, find by id/path | MIXED (connect ок; ensureMoyDen ломает) |
| C | Passport client | read/write Bridge, cache, settings/overview sync | COMPLETE как клиент API |
| D | Stage track UI | `readStageFromBridge`, `renderStageTrack`, `stage_model` | COMPLETE (модель с Bridge) |
| E | Project Chrome | верхняя панель + разделы | COMPLETE в dirty; **уже переносится** в split как UI-02 WIP |
| F | Boot / enter shell | `#bootScreen`, shellLevel, enterAppShell | MIXED |
| G | Create-story | storytelling UI поверх 5-step wizard | INCOMPLETE / MIXED |
| H | History navigation | `pushNavState` / `applyNavState` / popstate | MIXED (тянет shell) |
| I | Overview infographic | desktop info cards, passport about | MIXED с C/D |
| J | ensureMoyDen seed | автозапись «Мой день» в localStorage | INCOMPLETE / риск #6 |
| K | Sidebar removal / full layout | is-projects-full, без постоянного sidebar | MIXED с E/F/G |
| L | Косметика / leftover | мёртвые els, PNG вне HTML и т.п. | не UI-задача |

Mega-hunks в dirty файле (особенно CSS H00) **смешивают** E+F+G+D — в clean ветке переносить только вырезками.

---

## 5. Карта зависимостей

```text
Committed Bridge
  ├─ /api/project-stage/read + stage_model  →  UI-04 Stage track
  └─ /api/project-passport/* + project_id     →  UI-03 Passport+Identity+Connect

UI-01 Projects home (done)
  └─ UI-02 Project Chrome (WIP in split)
        └─ optional later: UI-05 shell cleanup (sidebar/boot) without breaking home

UI-03 Connect + identity + passport client  (A+B+C together — иначе бессмысленно)
  ├─ needs Bridge passport (done)
  └─ feeds overview passport display (I)

UI-04 Stage track on overview (D)
  ├─ needs Bridge stage (done)
  └─ ideally after or with overview surface (I)

UI-06 Create-new / create-story (G) — after connect OR parallel only if isolated
UI-07 History nav (H) — after stable shell/chrome
UI-08 ensureMoyDen (J) — fix or delete; do not ship as-is
```

---

## 6. Переносить / переработать / отложить / не переносить

| Решение | Группы | Комментарий |
|---|---|---|
| **Переносить (в worktree вручную)** | E→UI-02; A+B+C→UI-03; D→UI-04; части I | Минимальные срезы; без копирования всего файла |
| **Переработать** | G create-story; J MoyDen; рассинхрон passport write fail на create | Не тащить «как есть» |
| **Отложить** | F boot (если не нужен); H history; K полное удаление sidebar; mobile overflow shell | Отдельные задачи |
| **Не переносить** | L косметика без функции; повтор Bridge backend; `_verify_*`, Health Candidate docs в UI-коммиты; `__pycache__`; fixture timestamp noise | |

---

## 7–8. Порядок дальнейших коммитов (UI-02+)

### UI-02 — Project Chrome (следующий)

| | |
|---|---|
| **Цель** | Верхняя оболочка открытого проекта: имя, разделы, активный раздел, ← Проекты |
| **Файлы** | только `index.html` в `D:\AI_POS_UI_SPLIT` |
| **Зависимости** | UI-01 |
| **Критерии готовности** | открытие из таблицы показывает chrome; имя верно; переходы по существующим экранам; возврат на «Проекты»; home/search/sort/menu целы; нет page errors; нет history/passport/stage/create в diff |
| **Запреты** | `pushNavState`; connect/create; Passport; `project_id` antidupe; `stage_model`; create-story; ensureMoyDen; boot; `__pycache__` |
| **Статус** | код READY в WIP split; коммит не создан |

### UI-03 — Connect existing + identity + passport client

| | |
|---|---|
| **Цель** | Подключение папки: pick→review→confirm; антидубли; запись passport + `project_id` |
| **Файлы** | `index.html` (UI only) |
| **Зависимости** | Bridge passport (HEAD); UI-01; желательно UI-02 |
| **Критерии** | нет дублей; failed write не добавляет карточку; human errors; REVIEW_STANDARD / #6 учтены для picker |
| **Запреты** | повторный backend; create-story; stage track; history; ensureMoyDen as-is |

### UI-04 — Stage track (`stage_model`)

| | |
|---|---|
| **Цель** | Показать трек стадий с Bridge на обзоре/инфографике |
| **Файлы** | `index.html` |
| **Зависимости** | Bridge stage_model (HEAD); поверхность обзора |
| **Критерии** | только `stage_model` с API; пустая модель → скрыть трек; label map допустим |
| **Запреты** | собственный hardcoded список стадий как источник истины; запись stage UI-ом |

### UI-05 — Shell / boot / layout (опционально)

| | |
|---|---|
| **Цель** | Boot и/или упрощение sidebar без поломки UI-01/02 |
| **Зависимости** | UI-02 |
| **Отложить**, если не даёт пользовательской ясности | |
| **Запреты** | смешивать с create-story |

### UI-06 — Create new / create-story

| | |
|---|---|
| **Цель** | Законченный сценарий создания (не обёртка над старым 5-step) |
| **Зависимости** | folder APIs Bridge; желательно UI-03 для согласованного passport/`project_id` |
| **Критерии** | проект не считается созданным до реальной папки; passport write failure не оставляет «ложную» карточку |
| **Запреты** | коммитить незавершённый storytelling WIP |

### UI-07 — History navigation

| | |
|---|---|
| **Цель** | Back/forward по экранам без ломки chrome/home |
| **Зависимости** | стабильные UI-01…UI-02 (+ shell) |
| **Запреты** | тащить вместе с create/connect |

### UI-08 — ensureMoyDen / Observation #6 hygiene

| | |
|---|---|
| **Цель** | Убрать или исправить автоseed; не обходить picker записью в storage |
| **Зависимости** | UI-03 identity |
| **Решение** | переработать или удалить; **не** переносить as-is |

---

## 9. Риски (Governance / Passport / project_id / stage_model / Bridge / localStorage)

| Риск | Суть | Митигация в плане |
|---|---|---|
| **Две истины стадии** | `project.stage` (local) vs Engine `stage_model` | UI-04 только читает Bridge; подпись «Текущая работа» не выдавать за Engine |
| **Двойная идентичность** | `project.id` vs `passport.project_id` | UI-03: единый lookup; запрет ensureMoyDen с новым uid |
| **Passport ≠ localStorage** | write fail + push card; applyPassport не синхронизирует id | UI-03/06: write-first; мутации через живую запись |
| **Observation #6** | folder picker / fake storage для «предъявления» | Не сидировать storage в тестах как «продуктовый» путь; для create/connect — честный UI или явная оговорка |
| **Layered Knowledge / Freeze** | UI не меняет Accepted-контракты Stage/Analyzer | Только потребление уже committed Bridge API |
| **User First** | технические сообщения Bridge | human messages в UI; не светить JSON/CLI |
| **Смешанный mega-diff** | один dirty index ломает «1 коммит = 1 задача» | только worktree + ручной перенос |
| **localStorage как истина файлов** | список ≠ паспорт на диске | passport cache с Bridge; список — UX-индекс |

---

## 10. Посторонние и временные файлы (не в UI-коммиты)

### Основной проект (`D:\AI_Project_Operating_System`)

| Путь | Действие |
|---|---|
| `index.html` (грязная гора) | источник для вырезок; **не** коммитить целиком |
| `tools/local_bridge.py` (cosmetic leftover) | не смешивать с UI |
| `Projects/**/project_stage.json` timestamp noise | исключить |
| `assets/icons/android-chrome-192x192.png` | отдельно / не UI-02 |
| `tools/__pycache__/**` | никогда |
| `Governance/PROJECT_HEALTH_CANDIDATE_*.md` | отдельный Governance-контур |
| `_nav_check.js`, `_verify_*_out/` | временные evidence; не коммитить без решения |

### Worktree (`D:\AI_POS_UI_SPLIT`)

| Путь | Действие |
|---|---|
| `tools/__pycache__/**` | не staging |
| Temp screenshots вне репо | ок для REVIEW; не коммитить |
| Этот файл `docs/UI_RECONSTRUCTION_PLAN.md` | документация плана; коммитить отдельно от UI-кода по желанию |

---

## Сводка состояния (на момент аудита)

| Дерево | Ветка | HEAD | UI commit | WIP |
|---|---|---|---|---|
| Split | `ui/split-index` | `4851044` (UI-01) | UI-02 chrome unstaged | `index.html` + pycache |
| Main | `master` | `96e0498` | — | огромный dirty `index.html` + extras |

**Архитектурный вывод:** clean-ветка правильно разлагает dirty UI; контракты Bridge уже в истории; следующий чистый шаг — **UI-02 Project Chrome**, затем связка connect/passport/identity (**UI-03**), затем stage track (**UI-04**). Create-story, history и MoyDen не готовы к прямому переносу.
