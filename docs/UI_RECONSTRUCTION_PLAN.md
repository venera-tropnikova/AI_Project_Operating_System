# UI Reconstruction Plan — AI POS

| Поле | Значение |
|---|---|
| Document Type | UI reconstruction plan (факт + план переноса) |
| Status | **Active** |
| Core UI Reconstruction | **Completed** |
| Date (canonical update) | 2026-07-31 |
| Branch (clean UI) | `ui/split-index` @ `D:\AI_POS_UI_SPLIT` |
| Current HEAD | `c2b00ae749e703de02d45f80213eae9bc0268200` (`c2b00ae`) |
| Base (pre UI chain) | `96e0498` — Bridge passport API already in history |
| Source WIP (reference) | `D:\AI_Project_Operating_System` dirty `index.html` (вырезки, не цель коммитов) |
| Canon | `Governance/CONSTITUTION.md` (приоритет при конфликте) |
| Related | ADR-0002 Freeze; Observations #5–#6; `Standards/DEVELOPMENT_STANDARD.md`; `Standards/REVIEW_STANDARD.md`; User First |

**Режим документа:** фиксация аудита, статусов и порядка работ. Код этим файлом не изменяется.

**NEXT_TASK:** `UI-10` — Project Overview / целостный обзор проекта (scope бывшей группы I). Выбрано пользователем после закрытия Core; не автопорядок backlog.

---

## 0. Каноническая сводка статусов (актуально)

Единственная каноническая таблица текущего состояния UI Reconstruction.

| ID | Название | Статус | Коммит (short) | Примечание |
|---|---|---|---|---|
| **UI-01** | Главная «Проекты» | **Completed** | `9d892e5` | вход в demo восстановлен в `c503b47` (UI-09-FIX-01) |
| **UI-02** | Project Chrome | **Completed** | `fbf0992` | |
| **docs** | План UI Reconstruction | **Completed** *(снимок)* | `6005bd9` | этот файл обновляется отдельно (`5ce8b67`, `c2b00ae` и далее) |
| **UI-03** | Connect + identity + passport | **Completed** | `f1507c8` | |
| **UI-04** | Stage track (`stage_model`) | **Completed** | `5505371` | трек готов; UI-10 встраивает существующий stage track без переделки |
| **polish** | Текст пустой текущей задачи | **Completed** | `8add727` | не отдельный UI-ID плана |
| **UI-05** | Shell / boot / layout | **Deferred, optional** | — | не выполнена; backlog |
| **UI-06a** | Standalone Create (write-first) | **Completed** | `82b3a64` | |
| **UI-06b** | Create Storytelling | **Deferred, optional** | — | не выполнена; backlog |
| **UI-07** | History navigation | **Completed** | `85c0d9f` | |
| **UI-08** | ensureMoyDen / demo hygiene | **Completed** | `33d79d9` | |
| **I** | Project Overview / паспорт-инфографика | **→ UI-10** | часть в `5505371` | scope задачи **UI-10** (не отдельный backlog-item) |
| **K** | Полное снятие sidebar / layout cleanup | **Deferred** | — | связана с UI-05; backlog |
| **UI-09** | Итоговая приёмка UI Reconstruction | **Completed** | `c503b47` | **PASS** на `c503b47`; D-DEMO-ENTRY устранён в `c503b47` |
| **UI-10** | Project Overview / целостный обзор | **Next** | — | выбор пользователя; scope = группа I |

**Core UI Reconstruction: Completed** (после UI-09 PASS; закрывающий docs-коммит `c2b00ae`).

**Не выдавать за выполненные:** UI-05, UI-06b, группу K. Группа I не «Completed», пока не закрыт UI-10.

### Критерий завершения основной (Core) реконструкции

**Core UI Reconstruction — Completed:** UI-09 закрыт с результатом **PASS** на HEAD `c503b47`; канон закрытия Core зафиксирован в `c2b00ae`.

Первичный прогон UI-09 выявил дефект **D-DEMO-ENTRY** (кнопка «Посмотреть пример» была недоступна на главной «Проекты»). Устранён отдельной fix-задачей **UI-09-FIX-01** в коммите `c503b47`; повторная приёмка UI-09 — **PASS**.

UI-05, UI-06b и группа K остаются в **отдельном backlog** и **не входят** в Completed Core. Группа I переведена в активный scope **UI-10** по решению пользователя.

### Порядок после закрытия Core

1. Core UI Reconstruction закрыта (UI-09 PASS @ `c503b47`; docs `c2b00ae`).
2. Пользователь выбрал следующую задачу: **UI-10** (группа I).
3. UI-05, UI-06b и K остаются в backlog; **не** назначать их автоматически после UI-10.

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

### 1.3. Целевая карта экранов (Core + post-Core)

```text
Главная «Проекты» (таблица)     ← UI-01 Completed
        ↓ открытие строки
Project Chrome                    ← UI-02 Completed
  ├── Обзор                       ← UI-10 Next (группа I: passport-about + встроенный stage track UI-04)
  ├── Текущая задача / …          ← отдельный раздел (не подмена Обзора)
  └── ← Проекты + History API     ← UI-07 Completed

Отдельно в Core (Completed):
  Подключить существующий         ← UI-03
  Создать новый (write-first)     ← UI-06a
  Demo hygiene                    ← UI-08
  Приёмка Core                    ← UI-09 PASS

Backlog (не активный Next):
  Boot / sidebar cleanup          ← UI-05 Deferred, optional
  Create Storytelling             ← UI-06b Deferred, optional
  Полное снятие sidebar           ← группа K Deferred (с UI-05)
```

### 1.4. Обязательные правила переноса

1. Один коммит = одна законченная логическая UI-задача (`DEVELOPMENT_STANDARD`).
2. Backend/Bridge, уже в истории (`stage_model`, passport API), **не** включать повторно в UI-коммиты.
3. Не копировать целиком грязный `index.html`; переносить минимальный HTML/CSS/JS вручную.
4. Не подсаживать тестовые проекты и не писать в `localStorage` без действия пользователя.
5. Перед «значимым» UI-коммитом — предъявление результата (`REVIEW_STANDARD`); Observation #6 учитывать для сценариев с folder picker.
6. UI-09 **не** меняет продуктовый код: только приёмка и отдельные fix-задачи при дефектах.
7. UI-10 **не** переделывает stage track (UI-04): встраивает существующий трек в обзор без дублирования логики/`stage_model`.

---

## 2. Карта групп источника (справочно)

Источник: dirty main `index.html` на момент аудита 2026-07-30. Статусы ниже — относительно clean-ветки после Core (`c2b00ae`) и назначения UI-10.

| Группа | Условное имя | Статус в clean-ветке |
|---|---|---|
| A | Connect existing | Covered by **UI-03 Completed** |
| B | Identity / anti-dupe | Covered by **UI-03 Completed** (ensureMoyDen не переносился) |
| C | Passport client | Covered by **UI-03 Completed** (+ Create UI-06a) |
| D | Stage track UI | Covered by **UI-04 Completed** (UI-10 потребляет без переделки) |
| E | Project Chrome | Covered by **UI-02 Completed** |
| F | Boot / enter shell | **UI-05 Deferred, optional** |
| G | Create-story | **UI-06a Completed**; storytelling → **UI-06b Deferred** |
| H | History navigation | Covered by **UI-07 Completed** |
| I | Overview infographic | **Scope UI-10 Next** (см. §3 / §4a) |
| J | ensureMoyDen seed | Covered by **UI-08 Completed** (не переносить as-is; demo изолирован) |
| K | Sidebar removal / full layout | **Deferred**; связана с UI-05 |
| L | Косметика / leftover | не UI-задача Core |

---

## 3. Задачи плана (детали)

### UI-01 — Projects home — Completed (`9d892e5`)

Главная «Проекты»: таблица, empty state, поиск/фильтр/сортировка, меню строки, `loadProjects` / `saveProjects`.

### UI-02 — Project Chrome — Completed (`fbf0992`)

Верхняя оболочка открытого проекта: имя, разделы, активный раздел, «← Проекты».

### UI-03 — Connect + identity + passport — Completed (`f1507c8`)

Подключение папки: pick → review → confirm; антидубли; `passport.project_id` ↔ `project.id`; write-first.

### UI-04 — Stage track — Completed (`5505371`)

Трек стадий только из Bridge `stage_model`; пустая модель скрывает трек. **Не переделывать в UI-10** — только встроить в экран обзора без дублирования.

### UI-05 — Shell / boot / layout — Deferred, optional

Boot и/или упрощение sidebar без поломки UI-01/02. **Не выполнена.** Не смешивать с create-story. Backlog (не Next).

### UI-06a — Standalone Create (write-first) — Completed (`82b3a64`)

Законченный сценарий создания без storytelling и без 5-step wizard: папка на диске, passport, карточка только после успешной регистрации; recovery/retry.

### UI-06b — Create Storytelling / содержательный экран создания проекта — Deferred, optional

**Не выполнена.** Содержательный слой поверх/рядом с созданием проекта:

- `#createStoryScreen`;
- компоновка 60/40;
- форма описания проекта;
- материалы под карточками;
- textarea;
- микрофон;
- компактная строка интеллектуальных помощников.

Запрет плана сохраняется: не коммитить незавершённый storytelling WIP. Backlog (не Next).

### UI-07 — History navigation — Completed (`85c0d9f`)

Back/Forward между system home и стабильными разделами workspace; Create/Connect вне history — by design.

### UI-08 — ensureMoyDen / Observation #6 hygiene — Completed (`33d79d9`)

Session-demo изолирован от реальной папки и Bridge; автоseed ensureMoyDen не переносился.

### Группа I — Project Overview / паспорт-инфографика — scope UI-10

| | |
|---|---|
| **Уже выполнено** | stage track из `stage_model` (UI-04) |
| **Активный scope** | задача **UI-10** (Next) — passport-about, информационные карточки, целостный обзор |
| **Статус строки** | не отдельный backlog-item; прогресс = статус UI-10 |

### Группа K — Полное снятие старого sidebar и завершение layout cleanup — Deferred

Связана с UI-05. Backlog; не Next.

---

## 4. UI-09 — итоговая приёмка UI Reconstruction — Completed

| | |
|---|---|
| **Статус** | **Completed** |
| **Результат** | **PASS** на `c503b47` |
| **Продуктовый код в приёмке** | не изменять; дефекты — отдельными fix |
| **Суть** | Интеграционная визуальная и функциональная проверка UI-01–UI-08 |
| **Fix в рамках закрытия** | `c503b47` — UI-09-FIX-01: вход в demo на главной «Проекты» |

### Результат приёмки

- UI-09 **PASS** подтверждён повторным прогоном на HEAD `c503b47`.
- Дефект **D-DEMO-ENTRY** (недоступная кнопка «Посмотреть пример» из‑за всегда скрытого `#desktopStart`) **устранён** в `c503b47`: кнопка `#btnOpenExample` перенесена в toolbar главной «Проекты»; `openExample` и изоляция demo не менялись.
- Core UI Reconstruction после этого — **Completed** (docs `c2b00ae`).

### Критерии приёмки UI-09

1. Главная «Проекты» открывается корректно.
2. Project Chrome работает.
3. Connect связывает `project.id` с `passport.project_id`.
4. Create создаёт проект по write-first сценарию.
5. Stage track получает `stage_model` через Bridge.
6. Пустое состояние текущей задачи корректно.
7. Переходы System Home ↔ Workspace работают через History API.
8. Demo не обращается к реальной папке проекта.
9. Интерфейс проверен в браузере и на целевой ширине телефона.
10. Нет блокирующих ошибок консоли.
11. Результаты проверки предъявлены скриншотами.
12. Найденные дефекты оформляются **отдельными fix-задачами**, а не скрытыми правками внутри UI-09.

---

## 4a. UI-10 — Project Overview / целостный обзор проекта — Next

| | |
|---|---|
| **Статус** | **Next** |
| **Источник scope** | группа **I** (Partial → активный scope UI-10) |
| **Зачем сейчас** | После Core пункт «Обзор» обещает лицо проекта, а показывает экран текущей задачи; паспорт уже на диске (UI-03/06a), смысл проекта в UI почти не виден (принципы 8–10, User First) |
| **Зависимости** | UI-02 Chrome, UI-04 stage track (потребление), passport Bridge UI-03/06a |

### Scope (входит)

1. Видимый экран / панель **Обзор** (снять stub-подмену обзора экраном текущей задачи).
2. Понятная карточка проекта (passport-about + поля карточки): название, идея/цель, аудитория, ожидаемый результат, статус, путь человеческим языком.
3. Информационные блоки / простая инфографика обзора без технического JSON.
4. Разведение навигации **Обзор** vs **Текущая задача** (задача остаётся отдельным разделом).
5. **Встроить существующий stage track (UI-04)** в композицию обзора: один трек, без второй реализации `stage_model` и без параллельного дублирующего UI-трека.
6. Чтение passport / полей через уже существующий Bridge; human copy; проверка desktop/телефон + скриншоты (`REVIEW_STANDARD`).

### Вне scope (не входит)

- UI-05 / группа K (boot, снятие sidebar, layout cleanup).
- UI-06b (Create Storytelling).
- Project Health UI; сервисный слой (Observation #5).
- Смена контрактов Stage Engine / Analyzer / Freeze.
- Переделка Create / Connect / write-first.
- Переработка логики stage track / нового enum стадий (UI-04 остаётся источником трека).
- Obs #6 path-paste как отдельный эпик.

### Критерии результата UI-10

1. Раздел «Обзор» открывается и показывает **целостный обзор проекта**, а не экран текущей задачи.
2. Видны ключевые сведения о проекте понятным языком (название, идея/цель, аудитория, ожидаемый результат, статус; путь — по-человечески).
3. Stage track из UI-04 **встроен** в обзор; логика/`stage_model` **не** дублируется и **не** переписывается.
4. «Текущая задача» остаётся отдельным разделом и не подменяет Обзор.
5. Demo-изоляция (UI-08) и Core-сценарии Create/Connect/History не ломаются.
6. Нет блокирующих ошибок консоли; результат предъявлен скриншотами (desktop + телефон).

---

## 5. Карта зависимостей (актуально)

```text
Committed Bridge
  ├─ /api/project-stage/read + stage_model  →  UI-04 Completed (встраивается в UI-10)
  └─ /api/project-passport/* + project_id     →  UI-03 / UI-06a Completed; UI-10 читает project passport

UI-01 … UI-04, UI-06a, UI-07, UI-08  →  Completed
        ↓
UI-09 итоговая приёмка Core          →  Completed (PASS @ c503b47)
        ↓
Core UI Reconstruction               →  Completed (docs c2b00ae)
        ↓
UI-10 Project Overview (группа I)    →  Next
        ↓
Backlog (не автопорядок):
  UI-05 (optional) | UI-06b (optional) | группа K (Deferred)
```

---

## 6. Риски (Governance / Passport / project_id / stage_model / Bridge / localStorage)

| Риск | Суть | Митигация в плане |
|---|---|---|
| **Две истины стадии** | `project.stage` (local) vs Engine `stage_model` | UI-04 / UI-10 только читают Bridge; about ≠ Engine; «Текущая работа» не выдавать за Engine |
| **Двойная идентичность** | `project.id` vs `passport.project_id` | UI-03: единый lookup; ensureMoyDen as-is не переносить |
| **Passport ≠ localStorage** | write fail + push card | UI-03/06a: write-first; мутации через живую запись |
| **Observation #6** | folder picker / fake storage | Не сидировать storage как продуктовый путь |
| **Layered Knowledge / Freeze** | UI не меняет Accepted-контракты | Только потребление committed Bridge API |
| **User First** | технические сообщения Bridge | human messages в UI |
| **Смешанный mega-diff** | один dirty index | только worktree + ручной перенос |
| **localStorage как истина файлов** | список ≠ паспорт на диске | passport с Bridge; список — UX-индекс |
| **Дубль stage track** | второй трек в Обзоре | UI-10 встраивает UI-04, не копирует |

---

## 7. Посторонние и временные файлы (не в UI-коммиты)

| Путь | Действие |
|---|---|
| `tools/__pycache__/**` | никогда |
| Fixture passport noise / timestamp noise | исключить |
| Temp screenshots вне репо | ок для REVIEW; не коммитить без решения |
| Грязный main `index.html` | только источник вырезок |
| `Governance/PROJECT_HEALTH_CANDIDATE_*.md` | отдельный Governance-контур |
| Этот файл | документация плана; коммитить отдельно от продуктового UI-кода |

---

## 8. Предыдущий статус (исторический снимок, не канон)

> Снимок на момент первого аудита плана (2026-07-30). Сохранён для истории решений.
> **Не использовать как текущий статус.** Канон — §0.

| Дерево | Ветка | HEAD (тогда) | UI commit | WIP |
|---|---|---|---|---|
| Split | `ui/split-index` | `4851044` (UI-01) | UI-02 chrome unstaged | `index.html` + pycache |
| Main | `master` | `96e0498` | — | огромный dirty `index.html` |

Тогдашний вывод: следующий чистый шаг — UI-02 Project Chrome, затем UI-03, затем UI-04. Create-story, history и MoyDen не готовы к прямому переносу. UI-02 описывался как WIP (~+212 / −4) без `pushNavState`.

Группировка dirty UI (A–L) и исходные критерии UI-02…UI-08 из аудита сохраняют смысл как контекст разбиения; актуальные статусы — только в §0–§4a.
