# Implement MVP-First Road Damage Defect System with Future-Ready Architecture

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with `plans/PLANS.md`.

## Purpose / Big Picture

After this work, a beginner should be able to run a full web system where a user can register, log in, choose a YOLO model, upload an image, receive an annotated image with detections, and review saved history. This first delivery intentionally focuses on image inference while keeping clear seams for future upgrades such as real-time video streaming, stronger storage backends, and scalable deployment topology. Success is observable by running the backend and frontend, executing the image inference flow end-to-end, and verifying persisted history records linked to a user and model.

## Progress

- [x] (2026-03-21 00:00Z) Defined project preparation baseline and locked architecture defaults from PRD-aligned planning.
- [x] (2026-03-21 00:00Z) Created this canonical living ExecPlan with mandatory sections and milestone structure.
- [ ] Implement Milestone 1 foundations: repository scaffold, backend skeleton, frontend skeleton, environment bootstrap, and shared conventions.
- [ ] Implement Milestone 2 image inference MVP: auth, model registry, image upload, YOLO inference, annotated output, and history persistence.
- [ ] Implement Milestone 3 hardening: validation, observability, latency baselines, and integration tests.
- [ ] Implement Milestone 4 Phase 2 real-time streaming: WebSocket frame loop with fixed-per-session model and restart-on-model-change behavior.
- [ ] Finalize Outcomes & Retrospective with achieved behavior, gaps, and lessons.

## Surprises & Discoveries

- Observation: Repository currently has planning documents only and no app scaffold.
  Evidence: File listing shows only `plans/PLANS.md` and the PRD document.

- Observation: PRD requests Flask blueprint style in non-functional notes, but stack decision is FastAPI for tighter type-friendly API modeling and modern async handling.
  Evidence: Locked decision in prior preparation planning and captured in Decision Log below.

## Decision Log

- Decision: Build image inference MVP first and defer real-time streaming to Phase 2.
  Rationale: Image flow validates core model integration, persistence, auth, and UX with lower operational risk.
  Date/Author: 2026-03-21 / Codex

- Decision: Use React + TypeScript + Tailwind + shadcn/ui for frontend.
  Rationale: Fast delivery with component consistency and strong ecosystem support for dashboard workflows.
  Date/Author: 2026-03-21 / Codex

- Decision: Use FastAPI with modular route/service/repository architecture.
  Rationale: Keeps backend maintainable, testable, and ready for future service split while staying Python-native for YOLO integration.
  Date/Author: 2026-03-21 / Codex

- Decision: Use SQLite and local disk volume for v1, behind repository and storage abstractions.
  Rationale: Simplifies first deployment while preserving a low-friction migration path to PostgreSQL and object storage.
  Date/Author: 2026-03-21 / Codex

- Decision: Deploy v1 on Docker Compose on one VM, CPU-first with optional GPU profile.
  Rationale: Keeps operations approachable for a beginner and supports predictable local-to-server parity.
  Date/Author: 2026-03-21 / Codex

## Outcomes & Retrospective

This section will be updated at each major milestone completion. At project completion, this section must summarize delivered user-visible behavior, unresolved gaps, and lessons that should inform v2 architecture and operations.

## Context and Orientation

The repository currently contains planning files and no implementation code. This ExecPlan turns that empty baseline into a stepwise implementation guide for a novice. The application has two major runtime parts. The frontend is a browser interface with pages for authentication, dashboard, image inference, and history. The backend exposes HTTP APIs for authentication, model metadata, image inference, and history retrieval. The backend hosts a YOLO inference module that loads named models and executes image predictions. The system persists users and inference metadata in SQLite and stores image assets on a local mounted directory.

A model registry in this repository means a controlled list of model identifiers and metadata that the backend accepts for inference. The registry prevents unknown model names and gives the frontend a reliable selector list. A repository layer in this repository means a small Python module whose job is database access only, keeping SQL and persistence rules separate from request handlers.

The key files to create and evolve are: `backend/app/main.py` for app composition; `backend/app/api/` for endpoint modules; `backend/app/services/` for business logic such as inference and auth; `backend/app/repositories/` for SQLite data access; `backend/app/models/` for ORM entities; `backend/app/schemas/` for request/response models; `frontend/src/` for views and API clients; `infra/docker-compose.yml` for local/VM orchestration; and `docs/` for runbooks and contracts.

## Plan of Work

Milestone 1 establishes the codebase skeleton and shared conventions. Create frontend, backend, and infra directories with minimal runnable defaults and shared environment variable definitions. Add consistent naming, linting, and test commands so every contributor executes the same workflow. Create a thin health endpoint and frontend shell page to verify routing and container wiring.

Milestone 2 delivers the MVP behavior. Implement user registration and login with password hashing and JWT tokens. Add a model registry service that returns allowed models and validates model names. Implement image upload endpoint with file validation and inference service call. Persist inference job metadata, detection results, and image paths. Return annotated image path and detection payload. Build frontend pages and API hooks for authentication, image inference, model selection, and history browsing.

Milestone 3 improves reliability and operational quality. Add structured error envelopes, request identifiers, and inference timing logs. Add tests for auth flows, model validation, file validation, history retrieval, and inference success path. Measure baseline latency on sample images and capture results in docs. Ensure commands are repeatable and local volumes are preserved across restarts.

Milestone 4 introduces Phase 2 streaming. Add a WebSocket endpoint for frame streaming with fixed model per session. Implement session lifecycle rules where model switches require stream restart. Add frontend streaming controls and overlay rendering. Store session summaries in history and document CPU limitations and optional GPU mode.

## Concrete Steps

All commands below are run from repository root `D:\road_defect_detection\frondend-backend-system`.

Prepare structure and environment:

    mkdir backend frontend infra docs
    copy .env.example .env
    docker compose -f infra/docker-compose.yml up --build

Backend bootstrap and checks:

    cd backend
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Expected backend check:

    GET http://localhost:8000/health
    HTTP 200
    {"status":"ok"}

Frontend bootstrap and checks:

    cd frontend
    npm install
    npm run dev

Expected frontend check:

    Open http://localhost:5173
    Browser shows login page with link to register page.

MVP flow verification:

    1) Register a user.
    2) Login and store token in client state.
    3) Open image inference page.
    4) Select model and upload image.
    5) Receive annotated output and detections.
    6) Open history page and confirm persisted record.

## Validation and Acceptance

Milestone 1 is accepted when a novice can clone the repository, run documented commands, start backend and frontend locally, and see health and shell pages without editing code.

Milestone 2 is accepted when a user can register and login, run image inference with model selection, and retrieve saved history tied to that user. API responses must use the standard success/error envelope and include stable schema fields documented in contracts.

Milestone 3 is accepted when automated tests pass for auth, inference validation, and history retrieval; structured logs include request id, model name, inference duration, and error category; and baseline latency measurements are documented from a repeatable command.

Milestone 4 is accepted when WebSocket streaming works with fixed model per session, changing model requires restarting stream, and frontend displays overlays while preserving session stability.

## Idempotence and Recovery

Setup commands must be safe to rerun. Containerized services should tolerate repeated `docker compose up` calls without data loss by using explicit named volumes for SQLite and media directories. If backend dependency installation fails, recreate the virtual environment and rerun requirements installation. If schema migrations fail, restore database from backup copy and rerun migration from the last successful revision.

All destructive operations must require explicit operator confirmation in scripts and documentation. The default path in this repository is additive: create new migration files and preserve prior data until a verified backup is available.

## Artifacts and Notes

The following artifacts must be maintained while implementing:

    docs/contracts/openapi.yaml
    docs/ux-wireframes-and-flows.md
    docs/engineering/workflow-and-quality-gates.md
    docs/operations/runbook.md

When milestone work is done, capture concise evidence snippets such as:

    pytest
    24 passed in 8.52s

    curl http://localhost:8000/health
    {"status":"ok"}

    curl -H "Authorization: Bearer <token>" http://localhost:8000/history
    {"success":true,"data":{"items":[...]}}

## Interfaces and Dependencies

Use the following backend dependencies and keep them explicit in `backend/requirements.txt`: FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, passlib with bcrypt, python-jose, Ultralytics, Pillow, and pytest stack for tests.

Define these interfaces in backend services:

In `backend/app/services/model_registry.py`, define:

    class ModelRegistryService:
        def list_models(self) -> list[ModelMetadata]: ...
        def get_model(self, name: str) -> ModelMetadata: ...
        def validate_model_name(self, name: str) -> None: ...

In `backend/app/services/inference_service.py`, define:

    class InferenceService:
        def infer_image(self, image_path: str, model_name: str, user_id: int) -> InferenceResult: ...
        def get_inference(self, inference_id: str, user_id: int) -> InferenceResult: ...

In `backend/app/services/storage_service.py`, define:

    class StorageService:
        def save_upload(self, file_bytes: bytes, original_name: str) -> StoredMedia: ...
        def save_annotated(self, image_bytes: bytes, source_media_id: str) -> StoredMedia: ...

Frontend must expose API client modules that map directly to documented endpoints. Keep response and error types explicit in TypeScript and reject unknown payload shapes at boundaries.

---

Plan change note (2026-03-21 / Codex): Initial creation of the living ExecPlan from PRD and master preparation plan so implementation can proceed with novice-friendly, milestone-based guidance and explicit acceptance behavior.
