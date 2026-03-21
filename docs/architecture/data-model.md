# Data Model and Entity Relationships

This model is designed for SQLite-first deployment while keeping migration to PostgreSQL straightforward.

## Core Entities

### User

- `id` (integer primary key)
- `email` (unique)
- `password_hash`
- `role` (`admin` or `user`)
- `created_at`
- `updated_at`

### ModelRegistryEntry

- `name` (primary key text)
- `type`
- `status`
- `performance_notes`
- `created_at`
- `updated_at`

### InferenceJob

- `id` (UUID text)
- `user_id` (foreign key -> User)
- `model_name` (foreign key -> ModelRegistryEntry.name)
- `status` (`succeeded`, `failed`)
- `error_code` (nullable)
- `created_at`

### DetectionResult

- `id` (integer primary key)
- `inference_job_id` (foreign key -> InferenceJob)
- `label`
- `confidence`
- `bbox_x1`
- `bbox_y1`
- `bbox_x2`
- `bbox_y2`

### MediaAsset

- `id` (UUID text)
- `inference_job_id` (foreign key -> InferenceJob)
- `kind` (`original`, `annotated`)
- `file_path`
- `file_size_bytes`
- `mime_type`
- `created_at`

## Relationship Summary

- One `User` has many `InferenceJob`.
- One `InferenceJob` has many `DetectionResult`.
- One `InferenceJob` has many `MediaAsset`.
- One `ModelRegistryEntry` can be referenced by many `InferenceJob`.

## Migration-Ready Conventions

- Use integer/UUID/text types compatible with both SQLite and PostgreSQL.
- Avoid SQLite-only SQL features in repositories.
- Keep all schema changes through migration files (Alembic).