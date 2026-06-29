# Python Testing Conventions (Backend)

## File Organization
- Tests exist in the `tests/` directory
- Files must be named `test_*.py`
- Separate unit tests (`test_scraper.py`) and integration/CLI tests (`test_main.py`)

## Test Structure
- Framework: `pytest` + `pytest-asyncio` using `asyncio_mode = "auto"`
- Use descriptive names: `test_<action>_<condition>`
- Single assertion block per test when possible

## Mocking
- **Never make real network calls** in tests
- Mock browser interactions using `unittest.mock.AsyncMock`
- Mock environment variables using `monkeypatch.setenv`

## Execution
- Ensure 100% pass rate before committing: `pytest tests/ -v`
- Run from project root: `.venv/bin/python -m pytest tests/ -v`
