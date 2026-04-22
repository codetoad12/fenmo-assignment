import sqlite3
from typing import Generator

DB_PATH = 'expenses.db'


def _create_expenses_table(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id           TEXT PRIMARY KEY,
            amount_paise INTEGER NOT NULL,
            category     TEXT NOT NULL,
            description  TEXT NOT NULL,
            date         TEXT NOT NULL,
            created_at   TEXT NOT NULL
        )
    ''')


def _ensure_amount_paise(conn: sqlite3.Connection) -> None:
    columns = {
        row[1] for row in conn.execute('PRAGMA table_info(expenses)')
    }
    if 'amount_paise' in columns and 'amount' not in columns:
        return

    conn.execute('ALTER TABLE expenses RENAME TO expenses_old')
    _create_expenses_table(conn)
    amount_expr = 'CAST(ROUND(amount * 100) AS INTEGER)'
    if 'amount_cents' in columns and 'amount' not in columns:
        amount_expr = 'amount_cents'

    conn.execute('''
        INSERT INTO expenses (
            id,
            amount_paise,
            category,
            description,
            date,
            created_at
        )
        SELECT
            id,
            CAST(ROUND(amount * 100) AS INTEGER),
            category,
            description,
            date,
            created_at
        FROM expenses_old
    '''.replace('CAST(ROUND(amount * 100) AS INTEGER)', amount_expr))
    conn.execute('DROP TABLE expenses_old')


def init_db(conn: sqlite3.Connection) -> None:
    _create_expenses_table(conn)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            key        TEXT PRIMARY KEY,
            body_hash  TEXT NOT NULL,
            expense_id TEXT NOT NULL REFERENCES expenses(id)
        )
    ''')
    _ensure_amount_paise(conn)
    conn.commit()


def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
