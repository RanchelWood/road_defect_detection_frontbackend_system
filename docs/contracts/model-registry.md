# Model Registry Contract

The model registry is the single source of truth for selectable model presets across all inference engines and job types.

## Purpose

- Prevent unsupported model requests from reaching engine adapters.
- Publish stable model presets to frontend selectors.
- Enable multiple inference engines without changing frontend request shape.
- Carry capability metadata for future video/streaming routing.

## Current Implementation

- Registry is assembled at runtime from registered adapters.
- First active engine: `rddc2020-cli`.
- First preset set:
  - `rddc2020-imsc-last95`
  - `rddc2020-imsc-ensemble-test1`
  - `rddc2020-imsc-ensemble-test2`

Planned next engine/presets (design complete, code pending):

- `orddc2024-cli`
  - `orddc2024-phase1-ensemble`
  - `orddc2024-phase2-ensemble` (planned default for video jobs)

## Data Contract

Each model entry includes:

- `model_id`: stable public ID used by clients.
- `engine_id`: inference engine owner for this model preset.
- `display_name`: user-facing model name.
- `description`: short usage context.
- `status`: `active`, `deprecated`, or `disabled`.
- `performance_notes`: guidance on speed/accuracy tradeoffs.
- `runtime_type`: backend runtime type label (`cli`, `http`, `grpc`).

Planned capability fields for video/streaming routing:

- `supports_image`: `true|false`
- `supports_video`: `true|false`
- `supports_streaming`: `true|false`

Optional future metadata (not required by current frontend):

- `engine_config_json` (weights list, CLI arguments, threshold defaults)
- `supported_labels`
- `avg_latency_ms_cpu`
- `avg_latency_ms_gpu`

## Validation Rules

- `model_id` must exist and be `status=active` to create image or video job.
- Backend resolves `model_id -> engine_id + engine_config` before dispatch.
- `deprecated` models may be listed with warning metadata.
- `disabled` models must reject job creation with `INVALID_MODEL`.
- Planned video endpoint must reject models where `supports_video=false`.

## Multi-Engine Rule

Do not expose engine-specific internals directly in frontend requests. Frontend always submits `model_id`; backend resolves engine details through registry.

## Planning References

- `docs/architecture/orddc2024-integration-design.md`
- `docs/architecture/video-support-design.md`
- `docs/contracts/video-inference-job-contract.md`
