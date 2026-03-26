# Road Damage Defect System

This repository now includes a runnable Milestone 2 MVP:

- FastAPI backend with auth, model registry, async inference jobs, cancel support, job image endpoint, and history APIs
- React frontend with login/register, protected pages, image inference submission/polling/cancel, result rendering, history browsing, and theme toggle
- External first inference engine integration via `rddc2020` CLI adapter
- SQLite persistence for users, refresh sessions, and inference jobs
- Docker Compose template for single-VM style startup

## Quick Start (Local)

1. Copy env template:

```powershell
copy .env.example .env
```

2. Start backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Start frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

4. Open `http://localhost:5173/login`.

## Current MVP Endpoints

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

## Launch Guide

For a beginner-friendly startup walkthrough, read [docs/operations/launch-guide.md](/D:/road_defect_detection/frondend-backend-system/docs/operations/launch-guide.md).

## Validation Commands

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests
```

Frontend build check:

```powershell
cd frontend
npm run build
```

## Execution Plan

Implementation continues from:

- `plans/execplan-road-damage-system-mvp.md`
