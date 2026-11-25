# AGENTS.md — Rules for AI coding agents

This file tells any AI coding agent (Claude Code, Gemini CLI, Copilot, Cursor, etc.) how to work
in this repository. Read it fully before making changes.

## Project in one paragraph

AirWise is a FastAPI + vanilla JS web app that gives households personalised guidance during
severe urban smog. A deterministic rules engine decides risk, outdoor windows, recommendations and
impact numbers; Gemini only rewrites and prioritises that output into friendly language and powers
a scoped chat. See [docs/PRD.md](docs/PRD.md) and [docs/architecture.md](docs/architecture.md).

## Golden rules

1. **Read the relevant doc before changing an area.** Architecture → `docs/architecture.md`,
   UI → `docs/design-system.md` + `docs/accessibility.md`, AI → `docs/ai-design.md`, etc.
2. **Keep docs in sync with code.** If a change makes a doc wrong, update the doc in the same commit.
3. **One branch only: `main`.** Never create other branches (challenge rule).
4. **Never commit secrets.** Keys live in `.env` (git-ignored). Only `.env.example` is committed.
5. **The AI never produces numbers.** All impact figures come from `app/rules/`. Gemini output is
   validated against a schema and merged by recommendation `id`.
6. **Every new logic path needs a test.** Rules engine changes need table-driven unit tests.
7. **No `innerHTML` with dynamic data** in the frontend. Use `textContent` / DOM APIs.
8. **Accessibility is not optional.** Every UI change must pass the checklist in
   `docs/accessibility.md`.
9. **Keep the repo under 10 MB.** No binaries, datasets, videos or `node_modules` in git.
10. **No new dependency without a reason.** Prefer the standard library; justify additions in the
    commit message.

## Commands

| Task | Command |
|---|---|
| Install | `pip install -r requirements.txt -r requirements-dev.txt` |
| Run dev server | `uvicorn app.main:app --reload` |
| Lint + format | `ruff check . && ruff format .` |
| Type check | `mypy app` |
| Backend tests | `pytest --cov=app` |
| Frontend tests | `node --test tests/frontend` |
| Dependency audit | `pip-audit` |

## Where things live

```
app/        FastAPI backend (api/, rules/, services/, models/, core/)
static/     Frontend (index.html, css/, js/)
tests/      Backend (unit/, integration/) and frontend tests
docs/       Project documentation
```

## Definition of done

- [ ] Code follows `docs/code-style.md`; `ruff` and `mypy` pass
- [ ] Tests added/updated; all tests pass; coverage does not drop below 85 %
- [ ] Accessibility checklist passes for UI changes
- [ ] No secrets, no PII logged, inputs validated
- [ ] Related docs updated
- [ ] Commit message follows Conventional Commits (`feat:`, `fix:`, `docs:`, `test:` …)
