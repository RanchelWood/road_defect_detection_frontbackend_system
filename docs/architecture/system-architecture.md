# System Architecture (MVP-First, External Inference Adapter)

## Locked Technology Choices

- Frontend: React + TypeScript + Tailwind.
- Backend: FastAPI with route/service/model separation.
- Inference integration strategy: external engine adapters (active: `rddc2020-cli`, `orddc2024-cli`, `shiyu-grddc2022-cli`).
- Data: SQLite in v1 with migration-ready patterns.
- Media storage: local disk volume under backend-managed paths.
- Deployment: Docker Compose on one VM, CPU-first default.

## Runtime Topology for Current MVP

- `frontend`: browser UI, auth session handling, job polling/cancel UX.
- `backend`: auth, model listing, job lifecycle API, history API, and adapter orchestration.
- `inference runtimes` (sibling paths/services): execute engine-specific command(s) (`rddc2020`, `orddc2024`, `ShiYu_SeaView_GRDDC2022` active).

The backend does not hardcode one runtime path into API contracts. Jobs resolve through an adapter interface keyed by `engine_id` and `model_id`.

## Backend Module Boundaries (Implemented)

- `backend/app/api/routes`: request/response handlers (`/auth`, `/models`, `/inference/jobs`, `/history`).
- `backend/app/services`: business logic (auth, model registry, inference jobs, dispatch, adapter orchestration).
- `backend/app/services/adapters`: one adapter module per inference engine (`rddc2020.py`, `orddc2024.py`, `shiyu_grddc2022.py`).
- `backend/app/models`: ORM entities (`User`, `RefreshTokenSession`, `InferenceJob`).
- `backend/app/schemas`: API payload definitions.

Note: a dedicated `repositories` package is not implemented yet; service classes currently perform ORM queries directly.

## Multi-Engine Extension Contract

- Add new engine by implementing the `InferenceEngineAdapter` interface.
- Register adapter in engine registry with unique `engine_id`.
- Add model presets that map to that `engine_id`.
- Keep frontend request shape unchanged (`model_id` only).

## Planned Video Architecture (Post-MVP)

Video support is planned in two phases:

- Phase 4A: asynchronous video jobs (`create -> poll -> cancel`) using a frame-extraction and aggregation pipeline.
- Phase 4B: optional WebSocket streaming for near-real-time frame inference.

Planned first video default model is `orddc2024-phase2-ensemble` because it is speed-oriented compared to ORDDC Phase 1 on CPU.

## Phase Strategy

- Phase 1 complete: auth + health scaffold.
- Phase 2 complete: async image inference jobs via external `rddc2020` adapter.
- Phase 3 implementation complete through Milestone 3E: hardening + multi-engine onboarding (`orddc2024`, `shiyu-grddc2022`).
- Phase 3F planned: GRDDC2022 one-stage + two-stage demo preset after 3E stability evidence closes.
- Phase 4A planned: async video jobs.
- Phase 4B planned: WebSocket streaming path.

## Planning References

- `docs/architecture/orddc2024-integration-design.md`
- `docs/architecture/shiyu-grddc2022-integration-design.md`
- `docs/architecture/video-support-design.md`
- `docs/contracts/video-inference-job-contract.md`
- `docs/contracts/realtime-websocket-contract.md`
