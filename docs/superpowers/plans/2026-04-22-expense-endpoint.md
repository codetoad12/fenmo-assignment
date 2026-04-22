# Expense Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement POST /expenses and GET /expenses with idempotency, validation, filtering, and sorting backed by SQLite.

**Architecture:** Three new modules — `app/models.py` (Pydantic), `app/database.py` (SQLite), `app/expenses.py` (router) — wired into `app/main.py` via lifespan and `include_router`. Tests use an in-memory SQLite DB injected via FastAPI dependency override.

**Tech Stack:** FastAPI, Pydantic v2, sqlite3 (stdlib), pytest, httpx (TestClient)

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `app/models.py` | Pydantic request/response models |
| Create | `app/database.py` | SQLite init + `get_connection` dependency |
| Create | `app/expenses.py` | APIRouter: POST + GET /expenses |
| Modify | `app/main.py` | Wire lifespan, include router |
| Create | `tests/__init__.py` | Make tests a package |
| Create | `tests/conftest.py` | Shared fixtures (in-memory DB, TestClient) |
| Create | `tests/test_expenses.py` | All endpoint tests |
| Modify | `pyproject.toml` | Add dev deps (pytest, httpx) |
| Modify | `requirements.txt` | Keep prod-only (no test deps) |

---

## Task 1: Add dev dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add optional dev deps to pyproject.toml**

Replace the existing `pyproject.toml` with:

```toml
[project]
name = 'fenmo-assessment-app'
version = '0.1.0'
description = 'Deployable FastAPI app for the Fenmo SDE assessment.'
requires-python = '>=3.11'
dependencies = [
    'fastapi',
    'uvicorn',
]

[project.optional-dependencies]
dev = ['pytest', 'httpx']

[tool.uv]
package = false
```

- [ ] **Step 2: Install dev deps**

```bash
uv sync --extra dev
```

Expected: resolves pytest and httpx into `.venv`.

---

## Task 2: Create Pydantic models

**Files:**
- Create: `app/models.py`

- [ ] **Step 1: Create app/models.py**

```python
from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Annotated


class ExpenseIn(BaseModel):
    amount: Annotated[float, Field(gt=0)]
    category: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    date: date


class ExpenseOut(BaseModel):
    id: str
    amount: float
    category: str
    description: str
    date: date
    created_at: datetime
```

---

## Task 3: Create database module

**Files:**
- Create: `app/database.py`

- [ ] **Step 1: Create app/database.py**

```python
import sqlite3
from typing import Generator

DB_PATH = 'expenses.db'


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id          TEXT PRIMARY KEY,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            description TEXT NOT NULL,
            date        TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            key        TEXT PRIMARY KEY,
            body_hash  TEXT NOT NULL,
            expense_id TEXT NOT NULL REFERENCES expenses(id)
        )
    ''')
    conn.commit()


def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

---

## Task 4: Create expenses router

**Files:**
- Create: `app/expenses.py`

- [ ] **Step 1: Create app/expenses.py**

```python
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from .database import get_connection
from .models import ExpenseIn, ExpenseOut

router = APIRouter()


def _hash_body(body: ExpenseIn) -> str:
    canonical = json.dumps(
        body.model_dump(mode='json'), sort_keys=True
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


@router.post('/expenses', response_model=ExpenseOut, status_code=201)
def create_expense(
    body: ExpenseIn,
    idempotency_key: Annotated[str, Header()],
    conn: sqlite3.Connection = Depends(get_connection),
) -> ExpenseOut:
    body_hash = _hash_body(body)
    row = conn.execute(
        'SELECT * FROM idempotency_keys WHERE key = ?',
        (idempotency_key,),
    ).fetchone()

    if row is not None:
        if row['body_hash'] != body_hash:
            raise HTTPException(status_code=409, detail='Conflict')
        expense = conn.execute(
            'SELECT * FROM expenses WHERE id = ?',
            (row['expense_id'],),
        ).fetchone()
        return ExpenseOut(**dict(expense))

    expense_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        'INSERT INTO expenses VALUES (?, ?, ?, ?, ?, ?)',
        (
            expense_id,
            body.amount,
            body.category,
            body.description,
            body.date.isoformat(),
            created_at,
        ),
    )
    conn.execute(
        'INSERT INTO idempotency_keys VALUES (?, ?, ?)',
        (idempotency_key, body_hash, expense_id),
    )
    conn.commit()
    return ExpenseOut(
        id=expense_id,
        amount=body.amount,
        category=body.category,
        description=body.description,
        date=body.date,
        created_at=created_at,
    )


@router.get('/expenses', response_model=list[ExpenseOut])
def list_expenses(
    category: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = 'asc',
    conn: sqlite3.Connection = Depends(get_connection),
) -> list[ExpenseOut]:
    query = 'SELECT * FROM expenses'
    params: list[str] = []

    if category:
        query += ' WHERE category = ?'
        params.append(category)

    if sort == 'date':
        direction = 'DESC' if order == 'desc' else 'ASC'
        query += f' ORDER BY date {direction}'

    rows = conn.execute(query, params).fetchall()
    return [ExpenseOut(**dict(r)) for r in rows]
```

---

## Task 5: Wire main.py

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: Rewrite app/main.py**

```python
import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .database import DB_PATH, init_db
from .expenses import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    conn.close()
    yield


app = FastAPI(
    title='Fenmo Assessment App',
    version='0.1.0',
    lifespan=lifespan,
)

app.include_router(router)


@app.get('/')
def read_root() -> dict[str, str]:
    return {
        'message': 'Fenmo assessment app is ready',
        'status': 'ok',
    }


@app.get('/health')
def read_health() -> dict[str, str]:
    return {'status': 'healthy'}
```

- [ ] **Step 2: Smoke-test startup**

```bash
uv run uvicorn app.main:app --reload
```

Expected: server starts without errors. Open http://127.0.0.1:8000/health — returns `{"status":"healthy"}`. Stop with Ctrl+C.

---

## Task 6: Write tests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_expenses.py`

- [ ] **Step 1: Create tests/__init__.py**

Empty file:
```python
```

- [ ] **Step 2: Create tests/conftest.py**

```python
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection, init_db
from app.main import app


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def client(db_conn):
    def override():
        yield db_conn

    app.dependency_overrides[get_connection] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 3: Create tests/test_expenses.py**

```python
import pytest


VALID_BODY = {
    'amount': 12.50,
    'category': 'food',
    'description': 'lunch',
    'date': '2026-04-22',
}


# --- POST /expenses ---

def test_create_expense_returns_201(client):
    r = client.post(
        '/expenses',
        json=VALID_BODY,
        headers={'Idempotency-Key': 'key-1'},
    )
    assert r.status_code == 201
    data = r.json()
    assert data['amount'] == 12.50
    assert data['category'] == 'food'
    assert data['description'] == 'lunch'
    assert data['date'] == '2026-04-22'
    assert 'id' in data
    assert 'created_at' in data


def test_zero_amount_rejected(client):
    body = {**VALID_BODY, 'amount': 0}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-2'},
    )
    assert r.status_code == 422


def test_negative_amount_rejected(client):
    body = {**VALID_BODY, 'amount': -5}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-3'},
    )
    assert r.status_code == 422


def test_empty_category_rejected(client):
    body = {**VALID_BODY, 'category': ''}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-4'},
    )
    assert r.status_code == 422


def test_empty_description_rejected(client):
    body = {**VALID_BODY, 'description': ''}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-5'},
    )
    assert r.status_code == 422


def test_invalid_date_rejected(client):
    body = {**VALID_BODY, 'date': 'not-a-date'}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-6'},
    )
    assert r.status_code == 422


def test_idempotent_retry_returns_original(client):
    headers = {'Idempotency-Key': 'idem-1'}
    r1 = client.post('/expenses', json=VALID_BODY, headers=headers)
    r2 = client.post('/expenses', json=VALID_BODY, headers=headers)
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.json()['id'] == r2.json()['id']


def test_idempotent_retry_no_duplicate(client):
    headers = {'Idempotency-Key': 'idem-2'}
    client.post('/expenses', json=VALID_BODY, headers=headers)
    client.post('/expenses', json=VALID_BODY, headers=headers)
    r = client.get('/expenses')
    assert len(r.json()) == 1


def test_conflict_on_different_body(client):
    headers = {'Idempotency-Key': 'idem-3'}
    client.post('/expenses', json=VALID_BODY, headers=headers)
    other = {**VALID_BODY, 'amount': 99.99}
    r = client.post('/expenses', json=other, headers=headers)
    assert r.status_code == 409


# --- GET /expenses ---

def test_get_expenses_returns_list(client):
    client.post(
        '/expenses',
        json=VALID_BODY,
        headers={'Idempotency-Key': 'g-1'},
    )
    r = client.get('/expenses')
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_category_filter(client):
    client.post(
        '/expenses',
        json={**VALID_BODY, 'category': 'food'},
        headers={'Idempotency-Key': 'g-2'},
    )
    client.post(
        '/expenses',
        json={**VALID_BODY, 'category': 'travel'},
        headers={'Idempotency-Key': 'g-3'},
    )
    r = client.get('/expenses?category=food')
    data = r.json()
    assert len(data) == 1
    assert data[0]['category'] == 'food'


def test_sort_date_asc(client):
    client.post(
        '/expenses',
        json={**VALID_BODY, 'date': '2026-04-24'},
        headers={'Idempotency-Key': 'g-4'},
    )
    client.post(
        '/expenses',
        json={**VALID_BODY, 'date': '2026-04-21'},
        headers={'Idempotency-Key': 'g-5'},
    )
    r = client.get('/expenses?sort=date&order=asc')
    dates = [e['date'] for e in r.json()]
    assert dates == sorted(dates)


def test_sort_date_desc(client):
    client.post(
        '/expenses',
        json={**VALID_BODY, 'date': '2026-04-24'},
        headers={'Idempotency-Key': 'g-6'},
    )
    client.post(
        '/expenses',
        json={**VALID_BODY, 'date': '2026-04-21'},
        headers={'Idempotency-Key': 'g-7'},
    )
    r = client.get('/expenses?sort=date&order=desc')
    dates = [e['date'] for e in r.json()]
    assert dates == sorted(dates, reverse=True)
```

- [ ] **Step 4: Run tests (expect failures — modules don't exist yet)**

```bash
uv run --extra dev pytest tests/test_expenses.py -v
```

Expected: ImportError or collection errors (modules missing). Confirms tests are wired correctly.

---

## Task 7: Run full test suite and verify

- [ ] **Step 1: Run all tests**

```bash
uv run --extra dev pytest tests/test_expenses.py -v
```

Expected output (all 14 tests pass):

```
tests/test_expenses.py::test_create_expense_returns_201 PASSED
tests/test_expenses.py::test_zero_amount_rejected PASSED
tests/test_expenses.py::test_negative_amount_rejected PASSED
tests/test_expenses.py::test_empty_category_rejected PASSED
tests/test_expenses.py::test_empty_description_rejected PASSED
tests/test_expenses.py::test_invalid_date_rejected PASSED
tests/test_expenses.py::test_idempotent_retry_returns_original PASSED
tests/test_expenses.py::test_idempotent_retry_no_duplicate PASSED
tests/test_expenses.py::test_conflict_on_different_body PASSED
tests/test_expenses.py::test_get_expenses_returns_list PASSED
tests/test_expenses.py::test_category_filter PASSED
tests/test_expenses.py::test_sort_date_asc PASSED
tests/test_expenses.py::test_sort_date_desc PASSED
============== 13 passed in ...s ==============
```

If any test fails, investigate before committing.

---

## Task 8: Commit and push

- [ ] **Step 1: Stage all new and modified files**

```bash
git add app/models.py app/database.py app/expenses.py app/main.py \
        tests/__init__.py tests/conftest.py tests/test_expenses.py \
        pyproject.toml docs/
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: add POST and GET /expenses with idempotency and tests"
```

- [ ] **Step 3: Push**

```bash
git push origin main
```

Expected: branch pushed to remote. Verify at GitHub repo commit history.
