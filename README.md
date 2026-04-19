# F-Bank UI Testing Project

Проект для ручного и автоматизированного тестирования учебного сервиса перевода денег.

## Состав проекта

- `dist/` - выданная фронтенд-сборка приложения
- `tests/` - UI-тесты на `Selenium + pytest`
- `docs/manual_test_cases.md` - 5 ручных тест-кейсов
- `docs/bugreports/` - 2 баг-репорта
- `.github/workflows/selenium.yml` - CI workflow для GitHub Actions

## Найденные дефекты

1. Приложение принимает отрицательную сумму перевода.
2. Приложение принимает номер карты длиннее 16 цифр.

На каждый дефект добавлен отдельный автотест.

## Запуск автотестов (Git Bash)

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m pytest -v
```

Ожидаемый результат прогона:
- 1 тест `PASSED` (позитивный сценарий)
- 2 теста `FAILED` (фиксируют реальные дефекты)

## Ручной запуск приложения в браузере

```bash
cd dist
python -m http.server 8000 --bind 127.0.0.1
```

Открыть в обычном браузере Windows:

[http://127.0.0.1:8000/?balance=5000&reserved=0](http://127.0.0.1:8000/?balance=5000&reserved=0)

Если порт занят, используйте `8001`:

```bash
python -m http.server 8001 --bind 127.0.0.1
```
