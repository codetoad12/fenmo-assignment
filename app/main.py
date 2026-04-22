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
