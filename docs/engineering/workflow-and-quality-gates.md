# Engineering Workflow and Quality Gates

This workflow is beginner-friendly and aligned with external engine integration.

## Repository Conventions

- `backend/` FastAPI app, adapters, services, repositories, tests.
- `frontend/` React pages, components, API clients, and UI test assets.
- `infra/` compose files and environment templates.
- `docs/` contracts, architecture, runbooks, and planning docs.
- `plans/` living ExecPlans.

## Team Roles and Ownership

- Team Leader: triage owner, delegation owner, closure owner, junior developer guide, and **test-evidence reviewer**.
- Frontend Engineer: GUI, frontend state, navigation, and API integration handling in `frontend/`.
- Backend Engineer: API behavior, validation, persistence, and runtime integration in `backend/`.
- Test Engineer: **executes required test suites**, performs exploratory/manual validation, and submits reproducible evidence.

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

## Frontend Automation Stack (Implemented)

Status on 2026-03-23: implemented and validated on this repo.

Active tools:

- Vitest `v4.1.0` for fast unit/component regression checks.
- Playwright `v1.58.2` for browser-level end-to-end validation.
- jsdom `v24.1.3` pinned for compatibility with the current Vitest runtime in this environment.

Active command contract:

- `npm run test:unit` -> Vitest regression suite.
- `npm run test:unit:watch` -> Vitest watch mode.
- `npm run test:unit:coverage` -> Vitest coverage output (text + html).
- `npm run test:e2e` -> Playwright full e2e suite.
- `npm run test:e2e:smoke` -> Playwright smoke pack for critical paths.
- `npm run test:e2e:install` -> one-time Chromium runtime installation.
- Beginner usage guide: `docs/engineering/frontend-test-automation-guide.md`.

How this optimizes workflow:

- Faster bug isolation: Vitest catches frontend logic/state failures before browser-level testing.
- Reproducible evidence: Playwright provides trace/video/screenshot artifacts for triage and retest.
- Better ownership routing: unit failures are usually frontend-owned; smoke failures often indicate frontend/backend/integration ownership.
- Safer closure: verification is evidence-based, not verbal confirmation.

## Test Strategy by Layer

- Unit tests (backend): model validation, adapter argument mapping, CSV parser normalization.
- API integration tests (backend): auth, job creation, job polling, history retrieval.
- Engine adapter tests: success path, missing weight path, malformed output path.
- Concurrency tests: two jobs cannot overwrite outputs.
- Frontend unit/component tests (Vitest active):
  - timestamp normalization and elapsed timer formatting
  - API error mapping and 401 handling callbacks
- Browser E2E tests (Playwright active):
  - register/login/logout flow
  - protected route redirects
  - inference submit + polling + terminal rendering
- Test Engineer smoke checks for release candidates remain mandatory even with automation.

## Test Execution Ownership (Mandatory)

- Test Engineer executes required test commands for each feature/bug batch.
- Team Leader does not perform routine test execution; Team Leader verifies evidence quality and closure readiness.
- Engineers may run local checks during implementation, but gate signoff evidence must come from Test Engineer thread.

Required evidence from Test Engineer:

- Exact command lines executed.
- Pass/fail summary and failing test IDs when applicable.
- Relevant artifacts (Playwright traces/videos/screenshots).
- Retest decision: `close` or `re-triage`.

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
5. Test Engineer executes required suites and manual checks, then reports evidence:
   - pass -> `closed`
   - fail -> reopen to `triaged` with retest evidence.

Closure rule:

- No issue is closed without Test Engineer execution evidence.

Ownership rule:

- `frontend` -> Frontend Engineer
- `backend` -> Backend Engineer
- `integration` -> primary owner + secondary reviewer
- `unclear` -> short investigation task first

## Quality Gates

Current required gates (active now):

- Backend tests pass for backend changes.
- Frontend `npm run test:unit` passes for frontend logic changes.
- Frontend `npm run test:e2e:smoke` passes for auth/inference/history-impacting frontend changes.
- Frontend build (`npm run build`) passes.
- API contract changes reflected in docs.
- ExecPlan progress and Decision Log updated.
- Every bug/feature closure includes Test Engineer executed-command evidence.

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
