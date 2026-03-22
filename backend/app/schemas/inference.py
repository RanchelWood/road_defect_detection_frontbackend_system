from datetime import datetime
from typing import Literal

from pydantic import BaseModel


JobStatus = Literal["queued", "running", "succeeded", "failed"]


class ModelPresetPayload(BaseModel):
    model_id: str
    engine_id: str
    status: str
    performance_notes: str
    display_name: str
    description: str
    runtime_type: str


class InferenceJobCreatedPayload(BaseModel):
    job_id: str
    status: JobStatus
    model_id: str
    engine_id: str


class InferenceJobDetailPayload(BaseModel):
    job_id: str
    status: JobStatus
    model_id: str
    engine_id: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict[str, object] | None = None
    error: dict[str, object] | None = None