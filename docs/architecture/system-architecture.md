# System Architecture (MVP-First, External Inference Adapter)

## Locked Technology Choices

- Frontend: React + TypeScript + Tailwind + shadcn/ui.
- Backend: FastAPI with modular route/service/repository layers.
- Inference integration strategy: external engine adapters (first engine is `rddc2020-cli`).
- Data: SQLite in v1 with migration-ready patterns.
- Media storage: local disk volume behind storage abstraction.
- Deployment: Docker Compose on one VM, CPU-first default.

## Runtime Topology for Milestone 2

- `frontend`: browser UI and job polling UX.
- `backend`: auth, model registry, job lifecycle API, history API.
- `inference runtime` (sibling path/service): executes engine-specific command(s) for `rddc2020`.

The backend never assumes one hardcoded runtime. It routes jobs through an engine adapter interface.

## Backend Module Boundaries

- `api`: request/response handling (`/auth`, `/models`, `/inference/jobs`, `/history`).
- `services`: auth, model registry, job dispatcher, adapter orchestration.
- `services/inference_engines`: one adapter module per engine.
- `repositories`: persistence logic for users, jobs, media, history.
- `models`: ORM entities for users, jobs, models, assets.
- `schemas`: request/response payload definitions.

## Multi-Engine Extension Contract

- Add new engine by implementing `InferenceEngineAdapter` interface.
- Register engine in backend engine registry with unique `engine_id`.
- Add model entries mapped to that `engine_id`.
- Keep frontend and public API unchanged (engine resolved via `model_id`).

## Phase Strategy

- Phase 1 complete: auth + health scaffold.
- Phase 2 (current): async image inference jobs via external `rddc2020` adapter.
- Phase 3: hardening, observability, concurrency and reliability improvements.
- Phase 4: real-time streaming path.