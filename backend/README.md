# Backend (FastAPI)

This backend now includes Milestone 3C multi-engine MVP APIs:

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /models`
- `POST /inference/jobs`
- `POST /inference/jobs/{job_id}/cancel`
- `GET /inference/jobs/{job_id}`
- `GET /inference/jobs/{job_id}/image/{kind}`
- `GET /history`
- `DELETE /history/{job_id}`
- `DELETE /history`

Core behavior:

- SQLite persistence for users, refresh-token sessions, and inference jobs
- Async inference job lifecycle (`queued` -> `running` -> `succeeded/failed/cancelled`)
- Cooperative cancellation for queued/running jobs with explicit `cancelled` terminal state
- History listing supports `sort_by=time|id|name` and `sort_order=asc|desc`
- Standard API success/error envelopes with request metadata
- External engine adapter integration:
  - `rddc2020-cli`
  - `orddc2024-cli` (second engine)

## Runtime Notes (ORDDC2024)

- Default ORDDC python path: `D:\anaconda3\envs\orddc2024\python.exe`
- Default ORDDC root path: `D:\road_defect_detection\orddc2024-main`
- Required ORDDC cache folders: `models_ph1`, `models_ph2`

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
