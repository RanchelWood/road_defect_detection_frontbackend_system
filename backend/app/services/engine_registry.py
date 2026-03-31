from functools import lru_cache

from app.services.adapters.base import InferenceEngineAdapter
from app.services.adapters.orddc2024 import Orddc2024Adapter
from app.services.adapters.rddc2020 import Rddc2020Adapter
from app.services.adapters.shiyu_grddc2022 import ShiyuGrddc2022Adapter


class InferenceEngineRegistry:
    def __init__(self, adapters: list[InferenceEngineAdapter]) -> None:
        self._adapters = {adapter.engine_id: adapter for adapter in adapters}

    def list_adapters(self) -> list[InferenceEngineAdapter]:
        return list(self._adapters.values())

    def get_adapter(self, engine_id: str) -> InferenceEngineAdapter | None:
        return self._adapters.get(engine_id)


@lru_cache
def get_engine_registry() -> InferenceEngineRegistry:
    return InferenceEngineRegistry(adapters=[Rddc2020Adapter(), Orddc2024Adapter(), ShiyuGrddc2022Adapter()])

