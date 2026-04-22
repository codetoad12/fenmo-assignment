import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from .database import get_connection
from .models import ExpenseIn, ExpenseOut

router = APIRouter()


def _amount_to_paise(amount: Decimal) -> int:
    return int(amount * Decimal('100'))


def _paise_to_amount(paise: int) -> Decimal:
    return Decimal(paise) / Decimal('100')


def _expense_from_row(row: sqlite3.Row) -> ExpenseOut:
    data = dict(row)
    data['amount'] = _paise_to_amount(data['amount_paise'])
    del data['amount_paise']
    return ExpenseOut(**data)


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
        out = _expense_from_row(expense)
        return JSONResponse(
            content=json.loads(out.model_dump_json()),
            status_code=200,
        )

    expense_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        '''
        INSERT INTO expenses (
            id,
            amount_paise,
            category,
            description,
            date,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (
            expense_id,
            _amount_to_paise(body.amount),
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
    filter_category = category.strip() if category else None

    if filter_category:
        query += ' WHERE lower(category) = lower(?)'
        params.append(filter_category)

    if sort == 'date':
        direction = 'DESC' if order == 'desc' else 'ASC'
        query += f' ORDER BY date {direction}'

    rows = conn.execute(query, params).fetchall()
    return [_expense_from_row(r) for r in rows]
