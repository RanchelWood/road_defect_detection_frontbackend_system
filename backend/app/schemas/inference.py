from datetime import datetime
from typing import Literal

from pydantic import BaseModel


JobStatus = Literal["queued", "running", "succeeded", "failed"]


class ModelPresetPayload(BaseModel):
    model_id: str
    engine_id: str
    display_name: str
    description: str
    status: str
    performance_notes: str
    runtime_type: str


class InferenceJobCreatedPayload(BaseModel):
    job_id: str
    status: JobStatus
    model_id: str
    engine_id: str


class DetectionBBoxPayload(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionPayload(BaseModel):
    label: str
    confidence: float | None = None
    bbox: DetectionBBoxPayload


class MediaRefPayload(BaseModel):
    id: str
    kind: Literal["original", "annotated"]
    path: str


class InferenceJobResultPayload(BaseModel):
    model_id: str
    engine_id: str
    detections: list[DetectionPayload]
    image_refs: list[MediaRefPayload]
    duration_ms: int = 0


class InferenceJobDetailPayload(BaseModel):
    job_id: str
    status: JobStatus
    model_id: str
    engine_id: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: InferenceJobResultPayload | None = None
    error: dict[str, object] | None = None
