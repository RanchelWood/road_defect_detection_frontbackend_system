# MVP Scope Definition

This document narrows the PRD into an implementation-ready MVP while preserving room for future inference engines and feature upgrades.

## Product Goal

Deliver a web system where authenticated users submit road-defect image inference jobs, monitor job status, view annotated results, and review history.

## In Scope for MVP

- User registration/login using email/password and JWT access control.
- Model selector fed by backend model registry.
- Asynchronous image inference job API (`create job` + `poll status`).
- External inference integration for first engine: `rddc2020` command-line runtime.
- Persisted inference history per user with model and engine metadata.
- Docker Compose single-VM deployment path for frontend/backend plus inference integration runtime.
- Basic observability: request IDs, job state transitions, command execution timings, and standardized API errors.

## Out of Scope for MVP

- Real-time video or webcam streaming.
- Mid-session model switching for streaming workflows.
- Distributed queue infrastructure beyond local async job orchestration.
- Object storage as default media backend.
- Multi-tenant organization features and advanced RBAC.

## Phase 2 Scope (Planned Next)

- WebSocket streaming endpoint for frame-level detection.
- Streaming UI with overlay rendering and restart-on-model-change behavior.
- Streaming session summary persistence in history.

## MVP Acceptance Behaviors

- A user can register/login and access protected pages.
- User can select model, upload image, submit job, and receive `job_id` with `queued` status.
- User can poll until `succeeded` or `failed`.
- Success response includes annotated image reference, detections, model ID, engine ID, and timing.
- History page lists completed and failed jobs for authenticated user.
- Invalid token, invalid file, unsupported model, or engine failure returns documented error envelope.