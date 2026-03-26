import subprocess
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.adapters.base import AdapterExecutionError
from app.services.adapters.orddc2024 import Orddc2024Adapter


def _build_orddc_adapter(tmp_path, timeout_seconds: int = 5) -> tuple[Orddc2024Adapter, Path]:
    python_exe = tmp_path / "python.exe"
    python_exe.write_text("", encoding="utf-8")

    orddc_root = tmp_path / "orddc2024"
    orddc_root.mkdir(parents=True)
    (orddc_root / "inference_script_v2_Phase1.py").write_text("print('phase1')", encoding="utf-8")
    (orddc_root / "inference_script_v2_Phase2.py").write_text("print('phase2')", encoding="utf-8")
    (orddc_root / "models_ph1").mkdir(parents=True)
    (orddc_root / "models_ph2").mkdir(parents=True)

    settings = Settings(
        orddc2024_python_path=str(python_exe),
        orddc2024_root=str(orddc_root),
        orddc2024_timeout_seconds=timeout_seconds,
    )
    adapter = Orddc2024Adapter(settings=settings)

    input_image = tmp_path / "road.jpg"
    input_image.write_bytes(b"image-bytes")

    return adapter, input_image


def test_orddc_adapter_returns_engine_timeout_when_subprocess_hangs(tmp_path, monkeypatch):
    adapter, input_image = _build_orddc_adapter(tmp_path, timeout_seconds=1)
    model = next(item for item in adapter.list_models() if item.model_id == "orddc2024-phase1-ensemble")

    class _HangingProcess:
        def __init__(self, *args, **kwargs):
            _ = (args, kwargs)
            self.returncode = None

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="orddc", timeout=timeout or 0)

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = 1

        def wait(self, timeout=None):
            _ = timeout
            self.returncode = 1
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(subprocess, "Popen", _HangingProcess)

    with pytest.raises(AdapterExecutionError) as exc_info:
        adapter.run(
            input_image_path=str(input_image),
            job_workspace=str(tmp_path / "workspace"),
            model=model,
        )

    assert exc_info.value.code == "ENGINE_TIMEOUT"


def test_orddc_adapter_uses_absolute_command_paths_for_relative_workspace(tmp_path, monkeypatch):
    adapter, input_image = _build_orddc_adapter(tmp_path)
    model = next(item for item in adapter.list_models() if item.model_id == "orddc2024-phase2-ensemble")

    captured_command: list[str] = []

    class _SuccessfulProcess:
        def __init__(self, command, *args, **kwargs):
            _ = (args, kwargs)
            captured_command[:] = command
            self._command = command
            self.returncode = 0

        def communicate(self, timeout=None):
            _ = timeout
            image_root = Path(self._command[2])
            results_csv = Path(self._command[3])
            boxed_output = Path(self._command[4])

            image_name = next(image_root.iterdir()).name
            results_csv.write_text(f"{image_name},D00 1 2 3 4 D10 5 6 7 8\n", encoding="utf-8")
            (boxed_output / image_name).write_bytes(b"boxed-image")
            return "ok", "warning: harmless stderr"

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = 1

        def wait(self, timeout=None):
            _ = timeout
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(subprocess, "Popen", _SuccessfulProcess)
    monkeypatch.chdir(tmp_path)

    result = adapter.run(
        input_image_path=str(input_image),
        job_workspace="relative_workspace",
        model=model,
    )

    assert Path(captured_command[2]).is_absolute()
    assert Path(captured_command[3]).is_absolute()
    assert Path(captured_command[4]).is_absolute()
    assert Path(result.annotated_image_path).name == "road.jpg"
    assert len(result.detections) == 2
    assert result.detections[0]["label"] == "D00"
    assert result.detections[0]["confidence"] is None
    assert (tmp_path / "relative_workspace" / "run_log.md").exists()


def test_orddc_adapter_returns_runtime_error_with_traceback_tail(tmp_path, monkeypatch):
    adapter, input_image = _build_orddc_adapter(tmp_path)
    model = next(item for item in adapter.list_models() if item.model_id == "orddc2024-phase1-ensemble")

    class _FailingProcess:
        def __init__(self, *args, **kwargs):
            _ = (args, kwargs)
            self.returncode = 2

        def communicate(self, timeout=None):
            _ = timeout
            warnings_prefix = "\\n".join(f"WARNING LINE {index:04d}" for index in range(400))
            traceback_tail = (
                "Traceback (most recent call last):\\n"
                "  File \"inference_script_v2_Phase1.py\", line 123, in <module>\\n"
                "    raise ValueError('fatal boom')\\n"
                "ValueError: fatal boom"
            )
            return "", warnings_prefix + "\\n" + traceback_tail

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = 2

        def wait(self, timeout=None):
            _ = timeout
            return self.returncode

        def kill(self):
            self.returncode = 2

    monkeypatch.setattr(subprocess, "Popen", _FailingProcess)

    with pytest.raises(AdapterExecutionError) as exc_info:
        adapter.run(
            input_image_path=str(input_image),
            job_workspace=str(tmp_path / "workspace"),
            model=model,
        )

    assert exc_info.value.code == "ENGINE_RUNTIME_ERROR"
    assert "Traceback (most recent call last):" in exc_info.value.message
    assert "ValueError: fatal boom" in exc_info.value.message
    assert "WARNING LINE 0000" not in exc_info.value.message
