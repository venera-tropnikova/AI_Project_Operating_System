# CHANGE_PROTOCOL

Статус: Active  
Версия контура: Architecture Freeze v1.0  
Связь: PIPELINE.md, ADR-0002, CONSTITUTION.md

## 1. Назначение

Протокол описывает, как вносятся изменения в управляемый контур AI POS, пока действует Architecture Freeze v1.0.

## 2. Обязательный pipeline

Любое значимое изменение проходит:

```text
Observation → Hypothesis → Draft → Evidence → Candidate → Action Gate → Accepted
```

Нельзя объявлять изменение Accepted, минуя Action Gate.

## 3. Что считается значимым изменением при Freeze

- смена роли Orchestrator / Stage / Analyzer границы;
- перевод Health из Observation в Draft/Candidate/Accepted;
- назначение внешнему источнику (GitHub и т.п.) права автоматически закрывать stage/delivery;
- разморозка или расширение Architecture Freeze.

Косметические правки формулировок внутри уже Accepted-документов допускаются без нового ADR, если не меняют смысл решения; иначе — новый цикл pipeline / ADR.

## 4. Action Gate (кратко)

Перед Accepted человек подтверждает:

1. понятна цель изменения;  
2. понятна разрешённая область;  
3. поняты запреты и риски;  
4. есть критерии проверки результата.

ИИ не закрывает Gate единолично.

## 5. Emergency

Экстренные правки вне полного цикла допустимы только по отдельному Emergency-протоколу (см. контур Architecture Risks) с обязательным пост-фактум возвратом в pipeline.  
Freeze не отменяет необходимость следа решения.
