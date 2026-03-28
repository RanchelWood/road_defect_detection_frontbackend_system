# Project Summary: Road Damage Defect System

## 1) What This Project Does Right Now

This is a web-based road-damage inference system with authentication, model selection, async job execution, and history management.

Current implemented behavior:

- User registration, login, token refresh, logout.
- Protected frontend routes (`/dashboard`, `/inference`, `/history`).
- Image inference job creation with selected model.
- Async job lifecycle: `queued -> running -> succeeded/failed/cancelled`.
- Job polling and result display (detections + annotated image endpoint).
- Job cancellation for queued/running jobs.
- History page with pagination, model filter, sort controls, page-size selector (10/20/50), delete-one, and clear-all.
- Theme toggle (light/dark) persisted in UI.
- Dynamic engine-family filtering on inference page based on `/models`.

## 2) Basic System Structure

High-level architecture:

- `frontend` (React SPA): UI for auth, inference, and history.
- `backend` (FastAPI): auth/session handling, job orchestration, persistence, model registry, and adapter routing.
- External inference runtimes (outside this repo): `rddc2020`, `orddc2024`, `ShiYu_SeaView_GRDDC2022`.

Core routing pattern:

- Frontend submits `model_id`.
- Backend resolves `model_id -> engine adapter`.
- Adapter executes engine-specific CLI inference and normalizes output.

## 3) Repository Layout

- `backend/`
  - `app/api/routes`: REST endpoints
  - `app/services`: business logic, job flow, model registry, engine adapters
  - `app/models`: SQLAlchemy ORM models
  - `tests/`: backend tests
- `frontend/`
  - `src/pages`: page-level UI
  - `src/api`: API client wrappers
  - `tests/e2e`: Playwright tests
- `docs/`: architecture, contracts, workflow, operations docs
- `infra/`: compose/runtime templates
- `plans/`: living ExecPlan and planning artifacts

## 4) Tech Stack

Frontend:

- React 18 + TypeScript
- Vite
- React Router
- Tailwind CSS
- Vitest + Playwright

Backend:

- FastAPI + Uvicorn
- SQLAlchemy ORM
- SQLite by default
- JWT auth + refresh-token persistence
- bcrypt/passlib for password hashing
- Pillow-enabled overlay rendering with fallback to copied image if Pillow is unavailable at runtime

Inference integration:

- Adapter-based multi-engine architecture
- Active image engines: `rddc2020-cli`, `orddc2024-cli`, `shiyu-grddc2022-cli`

## 5) Data Layer (Current)

Default persistence is SQLite (environment-configurable `database_url`).

Core tables:

- `users`
- `refresh_tokens`
- `inference_jobs`

Notes:

- Jobs store `engine_id` and `model_id` as stable text references.
- Model presets are currently code-defined in engine adapters (no dedicated model table yet).

## 6) Key API Surface (Current)

- Health: `GET /health`
- Auth:
  - `POST /auth/register`
  - `POST /auth/login`
  - `POST /auth/refresh`
  - `POST /auth/logout`
- Models: `GET /models`
- Inference jobs:
  - `POST /inference/jobs`
  - `POST /inference/jobs/{job_id}/cancel`
  - `GET /inference/jobs/{job_id}`
  - `GET /inference/jobs/{job_id}/image/{kind}`
- History:
  - `GET /history`
  - `DELETE /history/{job_id}`
  - `DELETE /history`

## 7) Testing and Quality Workflow

Frontend checks:

- `npm run test:unit`
- `npm run test:e2e:smoke`
- `npm run build`

Backend checks:

- `python -m pytest tests`

Team workflow uses a verification-gated bug lifecycle with Team Leader, Frontend Engineer, Backend Engineer, and Test Engineer roles.

## 8) Current Status Snapshot

Based on current plan/docs state:

- Milestone 1, 2, 3, and 3E implementation are completed.
- Milestone 3F is planned.
- Milestone 4 is pending (video-focused async jobs, then optional real-time streaming path).

Practical interpretation:

- Image inference flow is end-to-end implemented with three active engines.
- Current in-sandbox verification has known environment blockers (`BUG-20260328-003`, `BUG-20260328-004`) that require local-host rerun evidence.
- Video capabilities are designed/planned but not yet in main runtime flow.
