# Backend (FastAPI)

This backend now includes Milestone 2 MVP APIs:

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /models`
- `POST /inference/jobs`
- `GET /inference/jobs/{job_id}`
- `GET /inference/jobs/{job_id}/image/{kind}`
- `GET /history`

Core behavior:

- SQLite persistence for users, refresh-token sessions, and inference jobs
- Async inference job lifecycle (`queued` -> `running` -> `succeeded/failed`)
- Standard API success/error envelopes with request metadata
- External engine adapter integration (`rddc2020-cli` first engine)

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
.\.venv\Scripts\python.exe -m pytest tests
```
