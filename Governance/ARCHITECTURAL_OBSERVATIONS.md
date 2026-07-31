# Architectural Observations

Статус: Active (журнал наблюдений)  
Версия контура: Architecture Freeze v1.0  
Pipeline: каждая Observation может породить Hypothesis по `PIPELINE.md`

---

## Architectural Observation #1

**Тема:** Двойная истина о стадии проекта  

**Наблюдение:**  
Если аналитический компонент (`project_analyzer` или ИИ-сводка) самостоятельно выбирает «текущую стадию», а Stage Engine считает стадию иначе, пользователь и автоматика получают две конкурирующие истины. Это разрушает смысл детерминированного Stage Engine и формализует удобную для исполнителя картину мира.

**Следствие для Freeze v1.0:**  
- стадия только в `project_stage.json` от Stage Engine;  
- analyzer читает и объясняет, не назначает;  
- Orchestrator вызывает Engine до analyzer.

**Связанные документы:** ORCHESTRATOR.md, HEALTH.md (не путать Health со Stage)

---

## Architectural Observation #2

**Тема:** Внешние системы дают evidence, но не завершают работу за человека  

**Наблюдение:**  
GitHub (releases, Pages, закрытые Issues, PR review, CI) и подобные источники дают сильные `system-confirmed` сигналы. Но закрытый Issue ≠ принятие результата в AI POS; commit message ≠ достаточное доказательство; отсутствие активности ≠ ARCHIVED/DELIVERED. Без этого различия система начнёт «закрывать» проекты без решения пользователя.

**Следствие для Freeze v1.0:**  
- адаптеры (в т.ч. GitHub) только поставляют evidence;  
- accept / archive / completion — приоритет user-confirmed;  
- архитектура обязана работать без GitHub.

**Связанные документы:** PIPELINE.md (Evidence ≠ Accepted), ADR-0002

---

## Architectural Observation #3

**Тема:** Несколько Candidate по одному Observation  

**Наблюдение:**  
Если несколько независимых Hypothesis, относящихся к одному Observation, одновременно достигают статуса Candidate, текущая модель Governance не определяет процедуру дальнейшего продвижения. Механизм разрешения остаётся предметом будущей проверки на практике.

**Следствие для Freeze v1.0:**  
- Observation может удерживать несколько Hypothesis (пример: Health A/B/C);  
- одновременный выход нескольких Candidate в Accepted не регламентирован каноном v1.0;  
- разрешение конфликта Candidate — вне текущего Freeze, проверяется практикой.

**Связанные документы:** PIPELINE.md, HEALTH.md, ADR-0002

---

## Architectural Observation #4

**Тема:** Расхождение статуса архитектурных документов Stage/Analyzer с фактом наличия MVP в репозитории  

**Наблюдение:**  
На момент аудита документы `PROJECT_STAGE_ENGINE.md` и `PROJECT_ANALYZER_AND_STAGE_BOUNDARY.md` содержали формулировки уровня «без реализации» / «реализация не начинается», тогда как в репозитории уже присутствовали `tools/project_stage_engine.py`, `tools/project_analyzer.py`, `tools/refresh_project_insight.py` и запись `.ai-pos/project_stage.json` / `project_analysis.json`. В том же контуре UI Overview отображает поле из записи проекта (`project.stage` в localStorage; подпись UI после решения Gate: «Текущая работа») отдельно от стадии, приходящей из CLI-анализа (`project_analysis.json`, стадия скопирована из Stage Engine).

**Связанные документы:** `PROJECT_STAGE_ENGINE.md`, `PROJECT_ANALYZER_AND_STAGE_BOUNDARY.md`, `Governance/ORCHESTRATOR.md`, `index.html`

---

## Правило журнала

Новые Architectural Observations добавляются как `#N` без удаления предыдущих.  
Переход Observation → Hypothesis фиксируется в DECISION_LOG / ADR по PIPELINE.md.
