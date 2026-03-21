# Model Registry Contract

The model registry is the single source of truth for selectable YOLO models in this system.

## Purpose

- Prevent unsupported model names from reaching inference service.
- Publish model metadata for frontend selector display.
- Support future model versioning and gradual deprecation.

## Data Contract

Each model entry includes:

- `name`: unique identifier used in API requests.
- `type`: currently `yolo`; reserved for future engine categories.
- `status`: `active`, `deprecated`, or `disabled`.
- `performance_notes`: human-readable speed/accuracy guidance.

Optional future fields:

- `version`
- `supported_defect_labels`
- `input_size`
- `avg_latency_ms_cpu`
- `avg_latency_ms_gpu`

## Initial Registry Entries

- `yolov8n` (fast, lower accuracy)
- `yolov8s` (balanced)
- `yolov8m` (higher accuracy)
- `custom-road-v1` (project-trained model)

## Validation Rules

- Inference request `model_name` must exist and have `status=active`.
- `deprecated` entries may remain listable but must return warning metadata.
- `disabled` entries must reject inference with `INVALID_MODEL`.