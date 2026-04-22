# Fenmo Assessment App

A focused expense tracker built for the Fenmo SDE technical assessment.
The goal was a working, deployable application with production-quality
reliability behavior — not maximum feature breadth.

## Submission Links

Live application: https://fenmo-assignment-p3ad.onrender.com/

GitHub repository: https://github.com/codetoad12/fenmo-assignment

## Local Setup

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000 — expense tracker UI
- http://127.0.0.1:8000/health — health check
- http://127.0.0.1:8000/docs — auto-generated API docs

## Run Tests

```bash
uv run --extra dev pytest tests/ -v
```

All 18 tests cover creation, validation, idempotent retry, conflict
detection, case-insensitive category filtering, and date sorting.

## Design Decisions

### FastAPI + stdlib sqlite3

FastAPI was chosen for its first-class Pydantic integration and automatic
OpenAPI docs. Using Python's built-in `sqlite3` instead of an ORM kept
the dependency footprint minimal and startup fast — both matter on Render
Free, which has a cold start penalty and a pip-based build step.

Pydantic v2 models handle all input validation declaratively. Invalid
amounts, blank strings, malformed dates, and future expense dates are
rejected at the boundary before any database work happens.

### Money handling

Amounts are accepted as `Decimal` values with at most two decimal places.
The database stores them as integer paise (`12.50` rupees becomes `1250`)
instead of floating-point values. This avoids rounding surprises that can
appear when storing money as `float`/SQLite `REAL`.

API responses serialize `Decimal` amounts as JSON strings. The frontend
parses those values for display and totals, while the backend remains the
source of truth for validation and storage.

### Idempotency via header + body hash

`POST /expenses` requires an `Idempotency-Key` header. The server stores
a SHA-256 hash of the canonical request body alongside the key. On retry:

- same key + same body → returns the original expense (no duplicate)
- same key + different body → returns 409 Conflict

This makes expense creation safe under slow networks, duplicate clicks,
and client-side retry buttons without requiring the client to track
server-assigned IDs. The idempotency table is a simple SQLite table —
no Redis or external cache needed.

Idempotency only protects one submission attempt. If the user submits the
same expense details again as a separate action, the frontend generates a
new idempotency key and the backend creates a new expense. This is
intentional because two identical-looking expenses can be legitimate.

### Vanilla JS served from the same FastAPI process

The frontend is plain HTML, CSS, and JavaScript served by FastAPI via
`StaticFiles` and `FileResponse`. No separate frontend deployment, no
build step, no CDN dependencies. The JS uses `crypto.randomUUID()` to
generate idempotency keys client-side and reuses the same key when
retrying after a network failure.

All API calls use relative URLs (`/expenses`, not `http://localhost:8000`)
so the same code works locally and on Render without configuration.

## What We Deliberately Avoided

**No ORM.** SQLAlchemy and similar tools add startup overhead, migration
machinery, and indirect SQL that is harder to audit. For two tables and
four endpoints, raw `sqlite3` is clearer and faster.

**No JavaScript framework or CDN.** React, Vue, and Alpine.js all
introduce either a build step or a CDN dependency. A CDN failure or slow
load would break the UI on a Render cold start. Vanilla JS is more
verbose but has zero external dependencies and loads instantly.

**No separate frontend deployment.** Serving the UI from the same FastAPI
process means one service, one Render instance, one URL, and no
cross-origin complexity.

**No optimistic UI updates.** The expense list always reflects what the
server confirmed. Optimistic inserts can diverge from server state,
especially under the retry scenarios this app is explicitly designed to
handle.

**No hard duplicate-expense block.** Two separate submissions with the
same amount, category, description, and date are allowed because they can
represent two real payments. Idempotency only deduplicates retries of the
same submission attempt.

**No background workers or persistent disk.** Render Free does not
provide persistent disk or always-on background jobs. The app is designed
to be stateless between restarts except for the SQLite file, which is
acceptable for a demo context.

## Tradeoffs

**SQLite in production.** SQLite serialises writes, so concurrent
requests will queue. For assessment and demo scale this is fine. A
production deployment with real users would migrate to Postgres — the
`sqlite3` calls are isolated in `app/database.py` to make that swap
straightforward.

**Idempotency keys have no TTL.** Keys are stored indefinitely. In
production you would expire them (e.g. 24 hours) and clean up the table.
For this assessment the table stays small and the simplicity is worth it.

**No pagination.** `GET /expenses` returns all matching rows. At
assessment scale (tens of records) this is fine. A production API would
add `limit`/`offset` or cursor-based pagination.

**Vanilla JS verbosity.** DOM manipulation and fetch handling in plain JS
is more boilerplate than a reactive framework. The tradeoff is zero build
tooling, instant load, and no framework version drift.

## Deployment (Render)

```text
Runtime:       Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Optional environment variable:

```text
EXPENSE_DB_PATH   Path to SQLite file (default: expenses.db)
```

Render Free instances spin down after inactivity. The first request after
a cold start may take a few seconds. The `/health` endpoint can be used
to verify the service is up before demoing.
