# Engineering Workflow and Quality Gates

This workflow is beginner-friendly and aligned with external engine integration.

## Repository Conventions

- `backend/` FastAPI app, adapters, services, repositories, tests.
- `frontend/` React pages, components, API clients, tests.
- `infra/` compose files and environment templates.
- `docs/` contracts, architecture, runbooks, and planning docs.
- `plans/` living ExecPlans.

## Team Roles and Ownership

- Team Leader: triage owner, delegation owner, closure owner, and junior developer guide.
- Frontend Engineer: GUI, frontend state, navigation, and API integration handling in `frontend/`.
- Backend Engineer: API behavior, validation, persistence, and runtime integration in `backend/`.
- Test Engineer: bug discovery, reproducible reporting, retest verification, and smoke regression evidence.

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

External engine runtime (`rddc2020`):

1. Ensure sibling path exists: `D:\road_defect_detection\rddc2020`.
2. Ensure engine dependencies and weights are available in that runtime.
3. Validate `detect.py` command manually before backend adapter integration tests.

## Test Strategy by Layer

- Unit tests: model validation, adapter argument mapping, CSV parser normalization.
- API integration tests: auth, job creation, job polling, history retrieval.
- Engine adapter tests: success path, missing weight path, malformed output path.
- Concurrency tests: two jobs cannot overwrite outputs.
- UI tests: submit -> poll -> success/failure rendering.
- Test Engineer smoke checks for release candidates:
  - register/login/logout
  - protected route redirect behavior
  - model load + image submit
  - job polling transition behavior
  - succeeded/failed rendering paths
  - history list/filter/pagination
  - deep-link to inference job
  - forced API failure UX
  - forced 401 redirect and session clear

## Bug Lifecycle and Verification Gate

Required status model:

- `new`
- `triaged`
- `in progress`
- `fixed`
- `needs retest`
- `closed`

Required flow:

1. User report or Test Engineer discovery creates a bug in `new`.
2. Team Leader triages ownership and severity, then marks `triaged`.
3. Assigned engineer works in `in progress` and submits fix as `fixed`.
4. Team Leader sends issue to Test Engineer and marks `needs retest`.
5. Test Engineer verifies:
   - pass -> `closed`
   - fail -> reopen to `triaged` with retest evidence.

Closure rule:

- No bug is closed without Test Engineer verification evidence.

Ownership rule:

- `frontend` -> Frontend Engineer
- `backend` -> Backend Engineer
- `integration` -> primary owner + secondary reviewer
- `unclear` -> short investigation task first

## Quality Gates

Before merge to main branch:

- Backend tests pass.
- Frontend tests/build pass.
- Adapter contract tests pass for first engine.
- API contract changes reflected in docs.
- ExecPlan progress and Decision Log updated.
- Every bug fix includes:
  - bug ID
  - owner note
  - retest result from Test Engineer before closure.

## Non-Functional Baselines

- Job creation endpoint p95 under 300ms (queue operation only).
- Job status polling endpoint p95 under 300ms.
- Inference job timing captured per engine/model for benchmarking.
- Every failed job logs `request_id`, `job_id`, `engine_id`, `model_id`, `error_code`.

## Security Checklist

- Password hashing with bcrypt.
- JWT validation on protected routes.
- File upload type and size validation.
- Server-side validation for `model_id` and job ownership.
- External command execution strictly from allowlisted model presets and paths.
- Secrets through env vars only.
