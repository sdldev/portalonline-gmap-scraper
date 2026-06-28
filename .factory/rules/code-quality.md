# Code Quality & Best Practices

## Code Length Rules (MANDATORY)
- **Max 30 lines per function** — if more, split into smaller functions
- **Max 400 lines per file** — if more, break into separate modules
- **Max 5 parameters per function** — use dataclass/TypedDict if more
- **Single responsibility per function** — one function, one job
- **Never write long functions** — split logic into helper functions

## Best Practices

### Naming
- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix `_` (e.g., `_helper_func`)
- Booleans: prefix `is_`, `has_`, `should_`

### Function Design
- **Pure functions** preferred over side effects
- **Early return** for guard clauses
- **Max 2 levels of nesting** — refactor into separate functions
- **Parameter object** if > 5 parameters

### File Organization
- **Imports at top**, ordered: stdlib → third-party → local
- **Constants** at start of file
- **Public API** first, private helpers last
- **One class per file** if class > 100 lines

### Error Handling
- **Specific exceptions** better than generic `Exception`
- **Fail fast** — validate input at the start
- **Log context** — add debugging info to error messages

### Comments
- **Self-documenting code** — clear function/variable names
- **Comment "why" not "what"** — code shows what, comment explains why
- **Docstring** for public API and complex functions
- **Remove dead code** — don't comment out old code

### Refactoring Triggers
Refactor if:
- Function > 30 lines
- File > 200 lines
- Nesting > 2 levels
- Parameters > 5
- Code duplication > 3 times
- Comments explaining complex code
