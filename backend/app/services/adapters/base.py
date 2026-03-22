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


class InferenceEngineAdapter(ABC):
    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Stable engine identifier."""

    @abstractmethod
    def list_models(self) -> list[ModelPreset]:
        """Return engine-backed model presets."""