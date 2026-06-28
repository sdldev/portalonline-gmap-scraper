# Python Conventions

## General
- Python 3.12+ features are standard
- Use modern type hinting (`str | None`, `list[int]`) instead of `typing` aliases
- All external calls must have explicit timeouts
- Use `pathlib.Path` over `os.path`

## Code Length & Splitting (MANDATORY)
- **Max 30 lines per function** — if more, split into smaller functions
- **Max 400 lines per file** — if more, break into separate modules
- **Max 5 parameters per function** — use dataclass/TypedDict if more
- **Single responsibility per function** — one function, one job
- **Never write long functions** — split logic into helper functions
- **Split example:**
  ```python
  # ❌ BAD: 80-line function
  async def process_data(data):
      # validation 10 lines
      # transform 20 lines
      # save 15 lines
      # notify 10 lines
      # cleanup 10 lines

  # ✅ GOOD: split into small functions
  async def process_data(data):
      validated = _validate_data(data)
      transformed = _transform_data(validated)
      await _save_to_db(transformed)
      await _notify_users(transformed)
      _cleanup_temp()
  ```

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
