# Backend (FastAPI)

This backend now includes the Milestone 1 runnable scaffold with:

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- SQLite persistence for users and refresh-token sessions
- Standard API success/error envelopes with request metadata

## Local Run

From repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend health check:

```powershell
curl http://localhost:8000/health
```

Expected response body shape:

```json
{
  "success": true,
  "data": { "status": "ok" },
  "meta": {
    "request_id": "...",
    "timestamp": "..."
  }
}
```

## Tests

```powershell
cd backend
python -m pytest tests
```