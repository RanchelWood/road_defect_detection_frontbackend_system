# Data Model and Entity Relationships

This model supports async job-based inference and multi-engine extensibility while remaining SQLite-first and PostgreSQL-ready.

## Core Entities

### User

- `id` (integer primary key)
- `email` (unique)
- `password_hash`
- `role` (`admin` or `user`)
- `created_at`
- `updated_at`

### InferenceEngine

- `id` (text primary key, example: `rddc2020-cli`)
- `display_name`
- `status` (`active`, `maintenance`, `disabled`)
- `runtime_type` (`cli`, `http`, `grpc`)
- `base_path_or_endpoint`
- `created_at`
- `updated_at`

### ModelRegistryEntry

- `id` (text primary key, stable `model_id` exposed to clients)
- `engine_id` (foreign key -> InferenceEngine.id)
- `model_key` (engine-local identifier or weight reference)
- `status` (`active`, `deprecated`, `disabled`)
- `performance_notes`
- `created_at`
- `updated_at`

### InferenceJob

- `id` (UUID text)
- `user_id` (foreign key -> User)
- `engine_id` (foreign key -> InferenceEngine.id)
- `model_id` (foreign key -> ModelRegistryEntry.id)
- `status` (`queued`, `running`, `succeeded`, `failed`)
- `engine_job_ref` (nullable external/internal runner reference)
- `input_path`
- `output_path` (nullable)
- `detections_json` (nullable)
- `error_code` (nullable)
- `error_message` (nullable)
- `created_at`
- `started_at` (nullable)
- `finished_at` (nullable)
- `duration_ms` (nullable)

### MediaAsset

- `id` (UUID text)
- `inference_job_id` (foreign key -> InferenceJob.id)
- `kind` (`original`, `annotated`)
- `file_path`
- `file_size_bytes`
- `mime_type`
- `created_at`

## Relationship Summary

- One `User` has many `InferenceJob`.
- One `InferenceEngine` has many `ModelRegistryEntry` and many `InferenceJob`.
- One `ModelRegistryEntry` is used by many `InferenceJob`.
- One `InferenceJob` can have multiple related `MediaAsset` records.

## Notes for `rddc2020` Integration

- Jobs must use per-job working/output directories.
- `results.csv` parsing output is normalized into `detections_json`.
- Engine failures are recorded in job error fields rather than dropped.

## Migration-Ready Conventions

- Keep schema changes through migration files.
- Use DB-agnostic query patterns in repositories.
- Preserve stable `model_id` contracts when adding engines.