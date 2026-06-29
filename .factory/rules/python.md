# Python Conventions (Backend)

For universal code quality rules (function length, file length, nesting limits, error handling, comments), see `code-quality.md`.

## Naming
- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private functions/attributes: prefix `_` (e.g., `_helper_func`)
- Booleans: prefix `is_`, `has_`, `should_`

## General
- Python 3.12+ features are standard
- Use modern type hinting (`str | None`, `list[int]`) instead of `typing` aliases
- All external calls must have explicit timeouts
- Use `pathlib.Path` over `os.path`

## Asynchronous Code
- Use `asyncio` patterns throughout
- Use `asyncio.sleep()` for non-blocking delays
- Catch specific async exceptions (`asyncio.TimeoutError`), not generic `Exception`

## Error Handling
- Use specific Exception types
- Inject JS error handlers into Playwright pages to suppress known driver crash bugs
- Log warnings before retrying, log errors before giving up

## Formatting
- Ruff is the source of truth
- Line length: 88
- Double quotes for strings
- Space indentation (4 spaces)
- Sort imports automatically via Ruff (`I` rule)
