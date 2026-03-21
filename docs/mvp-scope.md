# MVP Scope Definition

This document narrows the PRD into an implementation-ready MVP while preserving space for future feature additions.

## Product Goal

Deliver a web system where authenticated users can run YOLO image inference for road defects, receive annotated results, and review their inference history.

## In Scope for MVP

- User registration and login using email/password and JWT access control.
- Model selector for image inference using a backend-provided model registry.
- Image upload and inference execution with YOLO in backend process.
- Response payload containing annotated image reference and structured detections.
- Inference history persisted per user with selected model and timestamps.
- Docker Compose single-VM deployment path with CPU-first runtime.
- Basic observability: request IDs, inference timings, and standardized API errors.

## Out of Scope for MVP

- Real-time video or webcam streaming.
- Mid-session model switching for streaming workflows.
- Multi-tenant organization features and advanced RBAC policy enforcement.
- Distributed job queue workers for inference.
- Object storage integration as default storage backend.
- Horizontal scaling and multi-node orchestration.

## Phase 2 Scope (Planned Next)

- WebSocket streaming endpoint for frame-by-frame inference.
- Frontend streaming interface with overlay rendering.
- Stream session model lock and restart-on-model-change rule.
- Session summary persistence into history.

## MVP Acceptance Behaviors

- A new user can register, log in, and access protected pages.
- On image inference page, user can select a model and upload an image.
- Backend returns detection labels, confidences, and bounding boxes with annotated image location.
- History page lists past jobs for the authenticated user, including chosen model and time.
- Invalid token, invalid file, or unsupported model returns documented error envelope.
