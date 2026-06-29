# Code Quality & Best Practices (Universal)

Applies to both backend (Python) and frontend (Vue/TypeScript).

## Code Length Rules (MANDATORY)
- **Max 30 lines per function/method** -- if more, split into smaller functions
- **Max 400 lines per file** -- if more, break into separate modules
- **Max 5 parameters per function** -- group into config object (dataclass / TypedDict / interface)
- **Single responsibility per function** -- one function, one job

## Function Design
- **Pure functions** preferred over side effects
- **Early return** for guard clauses
- **Max 2 levels of nesting** -- refactor into separate functions
- **Parameter object** if > 5 parameters

## File Organization
- **Imports/dependencies at top** of file
- **Constants/config** at start of file
- **Public API/exports** first, private helpers last
- **One class/component per file** if > 100 lines

## Error Handling
- **Specific exceptions/errors** -- avoid generic catch-all
- **Fail fast** -- validate input at the start
- **Log context** -- add debugging info to error messages

## Comments
- **Self-documenting code** -- clear function/variable names
- **Comment "why" not "what"** -- code shows what, comment explains why
- **Docstring/JSDoc** for public API and complex functions
- **Remove dead code** -- don't comment out old code

## Refactoring Triggers
Refactor if:
- Function > 30 lines
- File > 200 lines (consider splitting above 200)
- Nesting > 2 levels
- Parameters > 5
- Code duplication > 3 times

## Language-Specific Naming
See `python.md` for Python naming conventions.
See `frontend.md` for Vue/TypeScript naming conventions.
