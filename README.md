# Fenmo Assessment App

Deployable FastAPI starter for the Fenmo SDE technical assessment.

## Local Setup

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Render Deployment

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Notes

This starter should be adapted to the assessment prompt once the timer starts.

