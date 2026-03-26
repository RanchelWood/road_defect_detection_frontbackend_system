# MVP Scope Definition

This document narrows the PRD into an implementation-ready MVP while preserving room for future inference engines and feature upgrades.

## Product Goal

Deliver a web system where authenticated users submit road-defect image inference jobs, monitor job status, cancel running work when needed, view annotated results, and review history.

## In Scope for MVP

- User registration/login using email/password and JWT access control.
- Model selector fed by backend model registry.
- Asynchronous image inference job API (`create job` + `poll status` + `cancel job`).
- External inference integration for first engine: `rddc2020` command-line runtime.
- Persisted inference history per user with model and engine metadata.
- History controls: page size, model filter, and sorting (`time|id|name`, `asc|desc`).
- Frontend usability additions: persisted model selection and persisted light/dark theme preference.
- Docker Compose single-VM deployment path for frontend/backend plus inference integration runtime.
- Basic observability: request IDs, job state transitions, command execution timings, and standardized API errors.

## Out of Scope for MVP

- Native real-time video or webcam streaming.
- Mid-session model switching for streaming workflows.
- Distributed queue infrastructure beyond local async job orchestration.
- Object storage as default media backend.
- Multi-tenant organization features and advanced RBAC.

## Post-MVP Video Roadmap (Planned)

- Phase 4A: async video jobs (`POST/GET/cancel`) with frame sampling and summary output.
- Phase 4B: WebSocket streaming (`/ws/inference`) for near-real-time frames after 4A stabilizes.
- Planned first video default model: `orddc2024-phase2-ensemble`.

## MVP Acceptance Behaviors

- A user can register/login and access protected pages.
- User can select model, upload image, submit job, and receive `job_id` with `queued` status.
- User can poll until `succeeded`, `failed`, or `cancelled`.
- User can cancel a queued/running job and see `cancelled` terminal state.
- Success response includes annotated image reference, detections, model ID, engine ID, and timing.
- History page lists user jobs with sorting and pagination controls.
- Invalid token, invalid file, unsupported model, or engine failure returns documented error envelope.

## Planning References

- `docs/architecture/video-support-design.md`
- `docs/contracts/video-inference-job-contract.md`
