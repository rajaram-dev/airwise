# Code Style — AirWise

Goal: code a reviewer can understand in one read. Consistency beats cleverness.

## 1. General

- Small, single-purpose functions (aim ≤ 30 lines).
- No magic numbers — thresholds and factors live in named constants (`rules/aqi.py`,
  `rules/catalog.py`).
- Names describe intent: `find_best_windows()`, not `calc2()`.
- Comments explain **why**, not what. Remove commented-out code.
- Fail loudly in development, softly for users (see error handling in architecture.md).

## 2. Python

| Rule | Tool / detail |
|---|---|
| Formatting | `ruff format` (Black-compatible, line length 100) |
| Linting | `ruff check` with rules `E, F, W, I, B, UP, N, S, SIM, C4, RUF` |
| Types | Type hints on all functions; `mypy app` with `strict = true` |
| Docstrings | Google style on public modules, classes and functions |
| Imports | Sorted by ruff (`I`); absolute imports from `app.` |
| Models | Pydantic v2 models with `model_config = ConfigDict(extra="forbid")` for inputs |
| Async | `async def` for I/O; pure logic in `rules/` stays sync and side-effect free |
| Errors | Raise domain exceptions (`AirDataUnavailable`, `AIUnavailable`); convert to HTTP in `core/errors.py` |
| Naming | `snake_case` functions/vars, `PascalCase` classes, `UPPER_CASE` constants |

Example:

```python
def classify_aqi(aqi: int) -> AqiCategory:
    """Return the US EPA category for an AQI value.

    Args:
        aqi: Air quality index, 0 or greater.

    Returns:
        The matching AqiCategory.
    """
    for upper_bound, category in AQI_BREAKPOINTS:
        if aqi <= upper_bound:
            return category
    return AqiCategory.HAZARDOUS
```

## 3. JavaScript

| Rule | Detail |
|---|---|
| Modules | Native ES modules; one responsibility per file |
| Variables | `const` by default, `let` when reassigned, never `var` |
| Globals | None; state lives in `state.js` |
| DOM | `textContent` and `createElement`; **never `innerHTML` with dynamic data** |
| Events | `addEventListener`; no inline `onclick` (CSP blocks it) |
| Async | `async/await` with `try/catch`; show user-friendly errors |
| Docs | JSDoc on exported functions with `@param` / `@returns` types |
| Formatting | 2-space indent, semicolons, single quotes, trailing commas |
| Naming | `camelCase` functions/vars, `UPPER_CASE` constants, `kebab-case` file names |
| Pure utils | Formatting and AQI helpers in `js/utils/` with no DOM access — unit-testable |

## 4. CSS

- Tokens only — no raw hex values outside `tokens.css`.
- BEM-style class names: `.rec-card`, `.rec-card__impact`, `.rec-card--highlight`.
- Mobile-first media queries with `min-width`.
- No `!important` except utility `.visually-hidden`.

## 5. HTML

- Semantic elements first; ARIA only when needed (see accessibility.md).
- Every `<img>`/icon has `alt` or `aria-hidden="true"`.
- One `<h1>`; headings in order.

## 6. Git

- Single branch: `main`.
- Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `style:`.
- Small commits, pushed regularly (the judges value visible progress).
- Never commit `.env`, media files or generated folders.

## 7. Project config (to be created with code)

- `pyproject.toml` — ruff, mypy, pytest and coverage settings
- `requirements.txt` / `requirements-dev.txt` — pinned versions
