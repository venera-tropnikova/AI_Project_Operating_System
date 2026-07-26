# Projects

Папка для шаблона проекта и тестовых фикстур AI POS.

## TEMPLATE

Каркас документов проекта (`PROJECT_CONTEXT.md`, `ROADMAP.md`, структура и др.) и каталог `.ai-pos/` для артефактов Stage Engine / Analyzer.

Используется как образец содержимого рабочей папки проекта и в smoke-проверках MVP.

## FIXTURES

Фиксированные мини-проекты для регрессии:

- `empty_no_stage` — крайние случаи stage/analysis;
- `mini_filled` — содержательные маркеры для проверки лестницы стадий MVP.

Запуск проверки: `python tools/mvp_smoke_check.py`.
