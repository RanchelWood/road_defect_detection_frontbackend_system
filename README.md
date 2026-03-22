# Road Damage Defect System

This repository now has a runnable Milestone 1 baseline:

- FastAPI backend scaffold with health + authentication flow
- React frontend scaffold with login/register/dashboard
- SQLite-backed user and refresh-token session storage
- Docker Compose template for single-VM style startup

Image inference and history features are still planned for Milestone 2.

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

## Milestone 1 Delivered Endpoints

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

## Validation Commands

Backend tests:

```powershell
cd backend
python -m pytest tests
```

Frontend build check:

```powershell
cd frontend
npm run build
```

## Execution Plan

Implementation must continue from:

- `plans/execplan-road-damage-system-mvp.md`