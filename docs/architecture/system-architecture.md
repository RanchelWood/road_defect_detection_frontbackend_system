# System Architecture (MVP-First, Future-Ready)

## Locked Technology Choices

- Frontend: React + TypeScript + Tailwind + shadcn/ui.
- Backend: FastAPI with modular route/service/repository layers.
- Inference: in-process Ultralytics model execution with cache.
- Data: SQLite in v1 with migration-ready access patterns.
- Media storage: local disk volume behind storage service abstraction.
- Deployment: Docker Compose on one VM, CPU-first with optional GPU path.

## Backend Module Boundaries

- `api`: HTTP request/response handling only.
- `services`: business logic for auth, inference, history, model registry, storage.
- `repositories`: persistence operations and query logic.
- `models`: ORM entities.
- `schemas`: request/response shape definitions.

## Extension Seams Reserved

- Storage interface to swap local disk with S3-compatible object storage.
- Repository abstraction to migrate SQLite to PostgreSQL.
- Inference service boundary to split inference into dedicated service.
- API contract stability so frontend does not break during backend migrations.

## Phase Strategy

- Phase 1 (MVP): auth + image inference + model selection + history.
- Phase 2: WebSocket real-time streaming with fixed model per session.