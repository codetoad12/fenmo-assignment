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
