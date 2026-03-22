# Model Registry Contract

The model registry is the single source of truth for selectable model presets across all inference engines.

## Purpose

- Prevent unsupported model requests from reaching engine adapters.
- Publish stable model presets to frontend selector.
- Enable multiple inference engines without changing frontend API shape.

## Data Contract

Each model entry includes:

- `model_id`: stable public ID used by clients.
- `engine_id`: inference engine owner for this model preset.
- `status`: `active`, `deprecated`, or `disabled`.
- `performance_notes`: guidance on speed/accuracy tradeoffs.

Optional backend-only metadata:

- `engine_config_json` (weights list, CLI arguments, threshold defaults)
- `supported_labels`
- `avg_latency_ms_cpu`
- `avg_latency_ms_gpu`

## Initial Engine and Presets (Phase 2)

Engine:

- `rddc2020-cli`

Initial model presets:

- `rddc2020-imsc-last95`
- `rddc2020-imsc-ensemble-test1`
- `rddc2020-imsc-ensemble-test2`

Each preset maps to a predefined CLI argument bundle in backend adapter configuration.

## Validation Rules

- `model_id` must exist and be `status=active` to create job.
- Backend resolves `model_id -> engine_id + engine_config` before dispatch.
- `deprecated` models may be listed with warning metadata.
- `disabled` models must reject job creation with `INVALID_MODEL`.

## Multi-Engine Rule

Do not expose engine-specific internals directly in frontend requests. Frontend always submits `model_id`; backend resolves engine details through registry.