# Engineering Workflow and Quality Gates

This workflow is written for beginner-friendly implementation with consistent team habits.

## Repository Conventions

Recommended structure:

- `backend/` FastAPI app, services, repositories, tests.
- `frontend/` React app, pages, components, API client, tests.
- `infra/` Docker Compose and environment templates.
- `docs/` product, contracts, runbooks, and migration notes.
- `plans/` living ExecPlans and requirement references.

## Environment Setup (Windows-Friendly)

Backend:

1. Install Python 3.11+.
2. Create virtual environment in `backend/.venv`.
3. Install dependencies from `backend/requirements.txt`.
4. Start backend with Uvicorn.

Frontend:

1. Install Node.js 20+.
2. Install dependencies in `frontend`.
3. Start dev server.

Container path:

1. Copy `.env.example` to `.env`.
2. Run `docker compose -f infra/docker-compose.yml up --build`.

## Test Strategy by Layer

- Unit tests: services and utility logic.
- API integration tests: auth, inference, history endpoints.
- UI tests: key component states and page flows.
- End-to-end happy path: register -> login -> infer image -> view history.

## Quality Gates

Before merge to main branch:

- Backend tests pass.
- Frontend tests pass.
- Lint checks pass (frontend and backend).
- API contract changes reflected in docs.
- ExecPlan progress and decision log updated.

## Non-Functional Baselines

- Image inference target: under 2 seconds on representative image and CPU baseline.
- API p95 target for non-inference endpoints: under 300ms in local benchmark.
- Every failed request logs request id and categorized error code.

## Security Checklist

- Password hashing with bcrypt.
- JWT validation on protected routes.
- File upload type and size validation.
- Server-side input validation on all payloads.
- Secrets only through environment variables, never hardcoded.