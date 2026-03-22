from app.services.adapters.base import ModelPreset
from app.services.engine_registry import InferenceEngineRegistry, get_engine_registry


class ModelRegistryService:
    def __init__(self, engine_registry: InferenceEngineRegistry | None = None) -> None:
        self._engine_registry = engine_registry or get_engine_registry()

    def list_models(self) -> list[ModelPreset]:
        models: list[ModelPreset] = []
        for adapter in self._engine_registry.list_adapters():
            models.extend(adapter.list_models())
        return models

    def get_model(self, model_id: str) -> ModelPreset | None:
        for model in self.list_models():
            if model.model_id == model_id:
                return model
        return None

    def validate_model_id(self, model_id: str) -> ModelPreset:
        model = self.get_model(model_id)
        if model is None:
            raise ValueError(f"Model '{model_id}' is not supported.")
        if model.status != "active":
            raise ValueError(f"Model '{model_id}' is not active.")
        return model