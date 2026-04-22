import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection, init_db
from app.main import app


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
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
