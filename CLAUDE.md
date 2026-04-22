# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dev Commands

```bash
# Install dependencies
uv sync

# Run locally with hot reload
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_expenses.py -v
```

Endpoints available locally: `http://127.0.0.1:8000`, `/health`, `/docs`

## Architecture

- `app/main.py` — FastAPI app instance, all routes registered here
- `render.yaml` — Render Free deployment config (build: `pip install -r requirements.txt`, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
- `pyproject.toml` — project metadata and deps (managed with `uv`)
- `requirements.txt` — pinned deps for Render's pip-based build

The app is a single-module FastAPI service. As endpoints are added, keep business logic in a service layer separate from route handlers. SQLite (stdlib `sqlite3`) is the persistence layer for local/demo use — no ORM.

---

# Fenmo Assessment Context

We are preparing for a timed Fenmo SDE technical assessment. The final
submission must include:

- a public live application URL
- a public GitHub repository URL
- a README with setup, run, test, and deployment notes
- a screenshot of the repository commit history page

The assessment is evaluated on depth and production-readiness rather than
feature breadth. Prioritize a focused, working, deployable application over a
large unfinished feature set.

## Current Project Scope

Build a full-stack expense tracker with a simple UI and a simple backend.
The first implementation milestone is the backend expense API.

Backend requirements:

- users can create an expense with `amount`, `category`, `description`,
  and `date`
- expense creation must behave reliably during client retries and network
  issues
- users can get expenses
- expense listing must support search/filtering by category
- expense listing must support sorting by date
- the minimum expense data model is `id`, `amount`, `category`,
  `description`, `date`, and `created_at`

Recommended retry strategy:

- require or support an `Idempotency-Key` header on `POST /expenses`
- the same key with the same request body should return the original expense
  without creating a duplicate
- the same key with a different request body should return `409 Conflict`

Suggested API shape:

- `POST /expenses`
- `GET /expenses`
- `GET /expenses?category=food`
- `GET /expenses?sort=date&order=asc`
- `GET /health`

Suggested backend stack:

- FastAPI
- Pydantic request and response models
- SQLite through the Python standard library for local/demo persistence
- pytest coverage for the core behavior

Backend acceptance criteria:

- valid `POST /expenses` requests create and return an expense
- invalid amounts, empty categories, empty descriptions, and invalid dates
  are rejected
- retrying `POST /expenses` with the same idempotency key and body does not
  create duplicates
- reusing an idempotency key with a different body returns `409 Conflict`
- `GET /expenses` returns stored expenses
- category filtering works
- date sorting works in ascending and descending order
- tests cover creation, validation, idempotent retry behavior, conflict
  behavior, category filtering, and date sorting

## Working Agreement

- Claude is expected to write the main application code.
- Codex focuses on planning, code review, style, tests, README polish, and
  production-readiness checks.
- Codex should break the problem into clear subtasks and hand those tasks to
  Claude with goals, expected files or modules, acceptance criteria, and
  constraints.
- Claude should ask clarifying questions when requirements, user flows, data
  models, or deployment expectations are ambiguous.
- Do not one-shot large parts of the solution unless there is a very high
  degree of confidence in the correct approach.
- Work through the app in small subtasks with short review loops owned by
  Codex.
- After each meaningful subtask, Claude should pause for Codex review before
  moving to broad new work unless the next step is obvious and low-risk.
- Before editing existing files, inspect the current workspace so changes from
  another assistant are preserved.
- Keep changes scoped to the assessment goal.

## Base Code Rules

- Keep every source line at or below 79 characters.
- Keep each function at or below 60 lines.
- Use single quotes for Python string literals unless double quotes avoid
  escaping or are required by a tool/framework.
- Prefer readable, explicit code over clever abstractions.
- Add comments only when they clarify non-obvious behavior.

## Likely Python Stack

Default to FastAPI for backend/API applications. Use Streamlit only if the
problem statement is primarily a dashboard, analytics, or data-entry app where
Streamlit gives a faster complete result.

For FastAPI apps, aim for:

- Pydantic request/response models
- clean route/service separation when useful
- SQLite or another simple persistence layer unless the prompt requires more
- health endpoint
- pytest coverage for core behavior
- Dockerfile or clear deploy instructions
- simple, polished UI if the prompt expects end-user interaction

## Render Free-Tier Strategy

Assume the first deployment target is Render Free unless the prompt clearly
requires paid infrastructure. Render Free is acceptable for this assessment,
but the app should be designed with these limits in mind:

- keep dependencies minimal and avoid heavy ML, browser automation, or large
  data packages unless the problem requires them
- avoid long startup work; startup should be fast and deterministic
- do not rely on local filesystem persistence for important data
- prefer SQLite only for demo/local state, or use an external database if the
  prompt truly needs durable hosted persistence
- avoid background workers, scheduled jobs, large in-memory queues, and
  unbounded file uploads
- do not rely on SSH access, scaling, one-off jobs, or persistent disks
- add pagination, limits, and validation for user-controlled inputs
- include `/health` so the deployed service can be checked quickly
- deploy early because builds can take several minutes even for a small app
- expect cold starts after idle time and verify the live URL before submission

Upgrade Render only if the actual prompt needs always-on behavior, more memory,
persistent disk, or a smoother evaluator demo than the free tier can provide.

## Time Strategy

1. Understand the problem statement and define the smallest complete product.
2. Build the core flow first.
3. Add persistence, validation, and errors.
4. Add tests for the highest-risk logic.
5. Polish the README and deployment settings.
6. Deploy, verify the live app, and prepare submission links.
