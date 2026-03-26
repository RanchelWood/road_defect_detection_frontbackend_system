# Data Model and Entity Relationships

This document describes the current persisted schema in this repository and the extension direction for future multi-engine growth.

## Current Persisted Entities (Implemented)

### User (`users`)

- `id` (integer primary key)
- `email` (unique)
- `password_hash`
- `role` (`admin` or `user`)
- `created_at`

### RefreshTokenSession (`refresh_token_sessions`)

- `id` (integer primary key)
- `user_id` (foreign key -> `users.id`)
- `refresh_token_hash`
- `expires_at`
- `created_at`

### InferenceJob (`inference_jobs`)

- `id` (UUID text primary key)
- `user_id` (foreign key -> `users.id`)
- `engine_id` (text)
- `model_id` (text)
- `status` (`queued`, `running`, `succeeded`, `failed`, `cancelled`)
- `input_path`
- `output_path` (nullable)
- `detections_json` (nullable)
- `duration_ms` (nullable)
- `original_filename`
- `error_code` (nullable)
- `error_message` (nullable)
- `created_at`
- `started_at` (nullable)
- `finished_at` (nullable)

## Relationship Summary (Current)

- One `User` has many `RefreshTokenSession` rows.
- One `User` has many `InferenceJob` rows.
- `InferenceJob` currently stores `engine_id` and `model_id` as stable text references (no FK table yet).

## Model Registry and Engine Metadata (Current Runtime)

- Model presets are defined in adapter code (currently `backend/app/services/adapters/rddc2020.py`).
- Registry lookup happens through service layer (`ModelRegistryService` + engine registry).
- History APIs include `model_id`, `engine_id`, and `original_filename` for UI rendering.

## Planned Extension Entities (Not Yet Persisted)

Future milestones may add explicit tables such as `InferenceEngine` and `ModelRegistryEntry` when dynamic model management is required. Current API contracts already use stable `engine_id`/`model_id` so this migration can be additive.

## Notes for `rddc2020` Integration

- Jobs run in per-job isolated workspace/output directories.
- Adapter output (`results.csv` + annotated image) is normalized into `detections_json` and `output_path`.
- Runtime cancellation is represented by terminal status `cancelled` with `JOB_CANCELLED` error code context.

## Migration-Ready Conventions

- Keep schema changes through migration files.
- Preserve stable `model_id` contracts when adding engines.
- Keep status semantics backward compatible (`cancelled` remains terminal).
