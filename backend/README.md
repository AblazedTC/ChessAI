# ChessAI backend

Minimal FastAPI backend. Chess-specific routes can be added to `main.py` as the
application grows.

## Setup

Run these commands in PowerShell from the `backend` directory with Python 3.10+
installed:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Development server

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

The API runs at http://127.0.0.1:8000.

- `GET /`: welcome message.
- `GET /health`: health check returning `{"status": "ok"}`.
- `/docs`: interactive Swagger UI.
- `/redoc`: alternative API documentation.
- `/openapi.json`: OpenAPI schema.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
