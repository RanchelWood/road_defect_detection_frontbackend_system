from collections.abc import Callable

from fastapi import BackgroundTasks

from app.core.config import get_settings


class InferenceDispatcher:
    def __init__(self, autorun_enabled: bool | None = None) -> None:
        if autorun_enabled is None:
            autorun_enabled = get_settings().inference_autorun_enabled
        self._autorun_enabled = autorun_enabled

    def dispatch(
        self,
        background_tasks: BackgroundTasks,
        job_id: str,
        execute_fn: Callable[[str], None],
    ) -> None:
        if not self._autorun_enabled:
            return
        background_tasks.add_task(execute_fn, job_id)