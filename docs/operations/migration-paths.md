# Migration Paths

This document captures explicit upgrade paths from MVP defaults to scalable alternatives.

## 1) SQLite -> PostgreSQL

- Keep repositories database-agnostic and avoid SQLite-specific SQL.
- Introduce PostgreSQL connection settings via env vars.
- Run schema migrations in PostgreSQL and validate compatibility tests.
- Perform staged cutover with data export/import and read-write verification.

## 2) Local Disk -> Object Storage

- Keep all media writes behind `StorageService` interface.
- Add object storage implementation (S3-compatible) without changing endpoint contracts.
- Migrate old media references incrementally with background copy.
- Switch default writer after validation.

## 3) CPU-only -> Optional GPU Runtime

- Maintain same inference API and service interfaces.
- Add runtime configuration to select YOLO device (`cpu` or `cuda`).
- Publish benchmark comparison before and after switch.
- Keep CPU fallback for unsupported hosts.

## 4) Monolith FastAPI -> Inference Service Split

- Extract inference module behind internal client interface.
- Move model loading/inference to dedicated service when load increases.
- Keep auth/history routes in core API service.
- Preserve external API contracts to avoid frontend breakage.