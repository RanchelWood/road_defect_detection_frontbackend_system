import subprocess

import pytest

from app.core.config import Settings
from app.services.adapters.base import AdapterExecutionError, ModelPreset
from app.services.adapters.rddc2020 import Rddc2020Adapter


def test_rddc_adapter_returns_engine_timeout_when_subprocess_hangs(tmp_path, monkeypatch):
    python_exe = tmp_path / "python.exe"
    python_exe.write_text("", encoding="utf-8")

    yolov5_root = tmp_path / "yolov5"
    yolov5_root.mkdir(parents=True)
    (yolov5_root / "detect.py").write_text("print('stub')", encoding="utf-8")

    weights_path = yolov5_root / "weights" / "IMSC"
    weights_path.mkdir(parents=True)
    (weights_path / "last_95.pt").write_bytes(b"weight-bytes")

    input_image = tmp_path / "road.jpg"
    input_image.write_bytes(b"image-bytes")

    settings = Settings(
        rddc2020_python_path=str(python_exe),
        rddc2020_yolov5_root=str(yolov5_root),
        rddc2020_timeout_seconds=1,
    )
    adapter = Rddc2020Adapter(settings=settings)
    model = ModelPreset(
        model_id="rddc2020-imsc-last95",
        engine_id="rddc2020-cli",
        display_name="Test Model",
        description="Test model",
        weights=("weights/IMSC/last_95.pt",),
    )

    class _HangingProcess:
        def __init__(self, *args, **kwargs):
            _ = (args, kwargs)
            self.returncode = None

        def communicate(self, input=None, timeout=None):
            _ = input
            raise subprocess.TimeoutExpired(cmd="detect.py", timeout=timeout or 0)

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
    assert "timeout" in exc_info.value.message.lower()
