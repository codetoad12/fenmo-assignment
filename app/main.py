import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import DB_PATH, init_db
from .expenses import router

TEMPLATES_DIR = Path(__file__).parent / 'templates'
STATIC_DIR = Path(__file__).parent / 'static'


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

app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
app.include_router(router)


@app.get('/')
def read_root() -> FileResponse:
    return FileResponse(TEMPLATES_DIR / 'index.html')


@app.get('/health')
def read_health() -> dict[str, str]:
    return {'status': 'healthy'}
