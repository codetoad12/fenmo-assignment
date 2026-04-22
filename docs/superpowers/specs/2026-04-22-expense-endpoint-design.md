# Expense Endpoint Design

**Date:** 2026-04-22
**Topic:** POST /expenses + GET /expenses with idempotency

## Scope

Implement the expense CRUD API (POST + GET) as the first backend milestone
for the Fenmo SDE assessment. The implementation uses Option B: a minimal
two-file split (database + router) with shared Pydantic models.

## Architecture

Three new modules added to `app/`:

- `app/database.py` — SQLite init and query functions (stdlib `sqlite3`)
- `app/models.py` — Pydantic request/response models
- `app/expenses.py` — FastAPI `APIRouter` with POST and GET handlers

`app/main.py` includes the router and runs `init_db()` via FastAPI `lifespan`.

## Data Model

```
expenses
  id          TEXT PRIMARY KEY   (UUID)
  amount      REAL NOT NULL
  category    TEXT NOT NULL
  description TEXT NOT NULL
  date        TEXT NOT NULL      (ISO 8601: YYYY-MM-DD)
  created_at  TEXT NOT NULL      (ISO 8601 datetime)

idempotency_keys
  key         TEXT PRIMARY KEY
  body_hash   TEXT NOT NULL      (SHA-256 of canonical JSON body)
  expense_id  TEXT NOT NULL      (FK -> expenses.id)
```

## API

### POST /expenses
- Header: `Idempotency-Key` (required)
- Body: `{ amount, category, description, date }`
- Same key + same body → 200 with original expense (no duplicate)
- Same key + different body → 409 Conflict
- New key → 201 Created with new expense
- Validation: `amount > 0`, `category` non-empty, `description` non-empty,
  `date` valid ISO date

### GET /expenses
- Query params: `category` (filter), `sort=date`, `order=asc|desc`
- Returns list of all matching expenses

## Pydantic Models

```python
class ExpenseIn(BaseModel):
    amount: float       # gt=0
    category: str       # min_length=1
    description: str    # min_length=1
    date: date

class ExpenseOut(ExpenseIn):
    id: str
    created_at: datetime
```

## Idempotency Strategy

1. Receive `Idempotency-Key` header and canonical JSON body hash (SHA-256).
2. Look up key in `idempotency_keys` table.
3. If found and hash matches → return stored expense (200).
4. If found and hash differs → return 409 Conflict.
5. If not found → insert expense, insert idempotency record, return 201.

## Testing

File: `tests/test_expenses.py` using `httpx.TestClient`.

Covers:
- Valid POST creates and returns expense
- Invalid amount (0, negative) returns 422
- Empty category or description returns 422
- Invalid date format returns 422
- Idempotent retry (same key + body) returns original, no duplicate
- Conflict (same key + different body) returns 409
- GET returns all expenses
- GET with `?category=` filters correctly
- GET with `?sort=date&order=asc` and `order=desc` sort correctly

## Constraints

- All lines ≤ 79 characters
- All functions ≤ 60 lines
- Single-quoted string literals throughout
- No ORM — use stdlib `sqlite3` directly
- In-memory SQLite (`:memory:`) for tests via dependency override
