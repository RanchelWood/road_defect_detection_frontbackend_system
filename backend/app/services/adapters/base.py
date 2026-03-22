from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPreset:
    model_id: str
    engine_id: str
    display_name: str
    description: str
    status: str = "active"
    performance_notes: str = ""
    runtime_type: str = "cli"
    weights: tuple[str, ...] = ()
    img_size: int = 640
    conf_thres: float = 0.2
    iou_thres: float = 0.9999
    agnostic_nms: bool = True
    augment: bool = True


@dataclass(frozen=True)
class AdapterExecutionResult:
    annotated_image_path: str
    detections: list[dict[str, object]]
    duration_ms: int


class AdapterExecutionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class InferenceEngineAdapter(ABC):
    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Stable engine identifier."""

    @abstractmethod
    def list_models(self) -> list[ModelPreset]:
        """Return engine-backed model presets."""

    @abstractmethod
    def run(self, input_image_path: str, job_workspace: str, model: ModelPreset) -> AdapterExecutionResult:
        """Run inference for one job and return normalized execution output."""