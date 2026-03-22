from app.services.adapters.base import InferenceEngineAdapter, ModelPreset


class Rddc2020Adapter(InferenceEngineAdapter):
    @property
    def engine_id(self) -> str:
        return "rddc2020-cli"

    def list_models(self) -> list[ModelPreset]:
        return [
            ModelPreset(
                model_id="rddc2020-imsc-last95",
                engine_id=self.engine_id,
                display_name="RDDC2020 IMSC Last95",
                description="Single-model preset using the IMSC last_95 weight.",
                performance_notes="Balanced speed and accuracy for MVP baseline.",
            ),
            ModelPreset(
                model_id="rddc2020-imsc-ensemble-test1",
                engine_id=self.engine_id,
                display_name="RDDC2020 IMSC Ensemble Test1",
                description="Ensemble preset tuned for road2020 test1-style images.",
                performance_notes="Higher accuracy, slower runtime due to multiple weights.",
            ),
            ModelPreset(
                model_id="rddc2020-imsc-ensemble-test2",
                engine_id=self.engine_id,
                display_name="RDDC2020 IMSC Ensemble Test2",
                description="Ensemble preset tuned for road2020 test2-style images.",
                performance_notes="Higher accuracy, slower runtime due to multiple weights.",
            ),
        ]