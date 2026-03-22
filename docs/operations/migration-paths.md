# Migration Paths

This document captures upgrade paths from MVP defaults to scalable multi-engine operations.

## 1) SQLite -> PostgreSQL

- Keep repositories DB-agnostic.
- Introduce PostgreSQL settings via env vars.
- Run migrations and validate job lifecycle compatibility.
- Perform staged cutover with data export/import verification.

## 2) Local Disk -> Object Storage

- Keep media writes behind storage service interface.
- Add object storage implementation without changing API contract.
- Migrate media references incrementally.

## 3) CPU-only -> Optional GPU Runtime

- Keep async job API unchanged.
- Add device policy per engine/model preset.
- Benchmark and publish latency/throughput changes.
- Keep CPU fallback.

## 4) Single External Engine -> Multiple Inference Engines

- Preserve `engine_id` + `model_id` contract in registry.
- Implement additional adapters under common engine interface.
- Add per-engine health and capability metadata.
- Keep frontend request shape stable (`model_id` only).

## 5) Local Sibling Runtime -> Managed Inference Service

- Move from local path (`D:\road_defect_detection\rddc2020`) to managed sidecar/remote service.
- Keep adapter interface; swap runtime transport (`cli` -> `http/grpc`).
- Preserve job and history schemas to avoid data migration churn.

## 6) Polling Jobs -> Event-Driven Updates

- Maintain `GET /inference/jobs/{job_id}` as compatibility baseline.
- Add optional push channel later (SSE/WebSocket) without breaking polling clients.