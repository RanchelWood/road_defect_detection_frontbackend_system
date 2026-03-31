import builtins
import subprocess
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.adapters.base import AdapterExecutionError
from app.services.adapters.shiyu_grddc2022 import ShiyuGrddc2022Adapter

VALID_IMAGE_BYTES = bytes.fromhex(
    "89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE0000000A49444154789C6360000000020001E527D4A20000000049454E44AE426082"
)


def _build_shiyu_root(tmp_path: Path) -> tuple[Settings, Path]:
    python_exe = tmp_path / "python.exe"
    python_exe.write_text("", encoding="utf-8")

    root = tmp_path / "shiyu"
    (root / "yolov7").mkdir(parents=True)
    (root / "yolov5" / "data").mkdir(parents=True)

    (root / "yolov7" / "detect.py").write_text("print('y7')", encoding="utf-8")
    (root / "yolov5" / "detect.py").write_text("print('y5')", encoding="utf-8")
    (root / "merge.py").write_text("print('merge')", encoding="utf-8")

    (root / "yolov7" / "YOLOv7x_640.pt").write_bytes(b"w")
    (root / "yolov5" / "YOLOv5x_640.pt").write_bytes(b"w")
    (root / "yolov5" / "data" / "rdd.yaml").write_text("names: []", encoding="utf-8")

    settings = Settings(
        shiyu_grddc2022_python_path=str(python_exe),
        shiyu_grddc2022_root=str(root),
        shiyu_grddc2022_device="cpu",
        shiyu_grddc2022_timeout_seconds_single=1,
        shiyu_grddc2022_timeout_seconds_ensemble=1,
    )

    return settings, root


def test_shiyu_adapter_ensemble_uses_absolute_paths_and_parses_merged_output(tmp_path, monkeypatch):
    settings, _ = _build_shiyu_root(tmp_path)
    adapter = ShiyuGrddc2022Adapter(settings=settings)
    input_image = tmp_path / "road.png"
    input_image.write_bytes(VALID_IMAGE_BYTES)

    commands: list[list[str]] = []

    class _SuccessfulProcess:
        def __init__(self, command, *args, **kwargs):
            _ = (args, kwargs)
            commands.append(command)
            self.command = command
            self.returncode = 0

        def communicate(self, timeout=None):
            _ = timeout
            cmd_text = " ".join(self.command)
            if "yolov7" in cmd_text and "detect.py" in cmd_text:
                project = Path(self.command[self.command.index("--project") + 1])
                name = self.command[self.command.index("--name") + 1]
                filename = self.command[self.command.index("--filename") + 1]
                out = project / name / filename
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text("road.jpg,1 1 2 3 4\n", encoding="utf-8")
            elif "yolov5" in cmd_text and "detect.py" in cmd_text:
                project = Path(self.command[self.command.index("--project") + 1])
                name = self.command[self.command.index("--name") + 1]
                filename = self.command[self.command.index("--filename") + 1]
                out = project / name / filename
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text("road.jpg,2 5 6 7 8\n", encoding="utf-8")
            elif self.command[1].endswith("merge.py"):
                Path(self.command[4]).write_text("road.jpg,4 10 20 30 40\n", encoding="utf-8")
            return "ok", ""

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
    monkeypatch.setattr(
        adapter,
        "_render_annotated_image",
        lambda source_image_path, detections, output_path: output_path.write_bytes(b"boxed"),
    )

    monkeypatch.chdir(tmp_path)
    model = next(item for item in adapter.list_models() if item.model_id == "shiyu-cpu-ensemble-default")
    result = adapter.run(str(input_image), "relative_workspace", model)

    assert len(commands) == 3
    assert commands[0][1].endswith("yolov7\\detect.py")
    assert commands[1][1].endswith("yolov5\\detect.py")
    assert "--no-trace" in commands[0]
    assert commands[2][1].endswith("merge.py")

    y7_source = Path(commands[0][commands[0].index("--source") + 1])
    y5_source = Path(commands[1][commands[1].index("--source") + 1])
    assert y7_source.is_absolute()
    assert y5_source.is_absolute()
    assert Path(commands[2][2]).is_absolute()
    assert Path(commands[2][3]).is_absolute()
    assert Path(commands[2][4]).is_absolute()

    assert [item["label"] for item in result.detections] == ["D40"]
    assert Path(result.annotated_image_path).exists()


def test_shiyu_adapter_timeout_maps_to_engine_timeout(tmp_path, monkeypatch):
    settings, _ = _build_shiyu_root(tmp_path)
    adapter = ShiyuGrddc2022Adapter(settings=settings)
    input_image = tmp_path / "road.png"
    input_image.write_bytes(VALID_IMAGE_BYTES)

    class _HangingProcess:
        def __init__(self, *args, **kwargs):
            _ = (args, kwargs)
            self.returncode = None

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="step", timeout=timeout or 0)

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

    model = next(item for item in adapter.list_models() if item.model_id == "shiyu-yolov7x-640")
    with pytest.raises(AdapterExecutionError) as exc_info:
        adapter.run(str(input_image), str(tmp_path / "workspace"), model)

    assert exc_info.value.code == "ENGINE_TIMEOUT"


def test_shiyu_adapter_missing_weights_is_deterministic(tmp_path, monkeypatch):
    settings, root = _build_shiyu_root(tmp_path)
    (root / "yolov5" / "YOLOv5x_640.pt").unlink()

    adapter = ShiyuGrddc2022Adapter(settings=settings)
    input_image = tmp_path / "road.png"
    input_image.write_bytes(VALID_IMAGE_BYTES)
    model = next(item for item in adapter.list_models() if item.model_id == "shiyu-cpu-ensemble-default")

    commands: list[list[str]] = []

    class _Y7OnlyProcess:
        def __init__(self, command, *args, **kwargs):
            _ = (args, kwargs)
            commands.append(command)
            self.command = command
            self.returncode = 0

            if "yolov5" in " ".join(command):
                raise AssertionError("yolov5 process should not be spawned when yolov5 weights are missing")

        def communicate(self, timeout=None):
            _ = timeout
            cmd_text = " ".join(self.command)
            if "yolov7" in cmd_text and "detect.py" in cmd_text:
                project = Path(self.command[self.command.index("--project") + 1])
                name = self.command[self.command.index("--name") + 1]
                filename = self.command[self.command.index("--filename") + 1]
                out = project / name / filename
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text("road.jpg,1 1 2 3 4\n", encoding="utf-8")
            return "ok", ""

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = 1

        def wait(self, timeout=None):
            _ = timeout
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(subprocess, "Popen", _Y7OnlyProcess)

    with pytest.raises(AdapterExecutionError) as exc_info:
        adapter.run(str(input_image), str(tmp_path / "workspace"), model)

    assert exc_info.value.code == "WEIGHTS_MISSING"
    assert "[yolov5_detect]" in exc_info.value.message
    assert len(commands) == 1
    assert commands[0][1].endswith("yolov7\\detect.py")

def test_shiyu_adapter_missing_target_row_raises_parse_error(tmp_path, monkeypatch):
    settings, _ = _build_shiyu_root(tmp_path)
    adapter = ShiyuGrddc2022Adapter(settings=settings)
    input_image = tmp_path / "road.png"
    input_image.write_bytes(VALID_IMAGE_BYTES)

    class _SuccessWithDifferentTarget:
        def __init__(self, command, *args, **kwargs):
            _ = (args, kwargs)
            self.command = command
            self.returncode = 0

        def communicate(self, timeout=None):
            _ = timeout
            if "yolov7" in " ".join(self.command):
                project = Path(self.command[self.command.index("--project") + 1])
                name = self.command[self.command.index("--name") + 1]
                filename = self.command[self.command.index("--filename") + 1]
                out = project / name / filename
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text("another.jpg,1 1 2 3 4\n", encoding="utf-8")
            return "ok", ""

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = 1

        def wait(self, timeout=None):
            _ = timeout
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(subprocess, "Popen", _SuccessWithDifferentTarget)

    model = next(item for item in adapter.list_models() if item.model_id == "shiyu-yolov7x-640")
    with pytest.raises(AdapterExecutionError) as exc_info:
        adapter.run(str(input_image), str(tmp_path / "workspace"), model)

    assert exc_info.value.code == "ENGINE_OUTPUT_PARSE_ERROR"
    assert "Missing detection row for target 'road'" in exc_info.value.message
    assert "y7_result.txt" in exc_info.value.message


def test_shiyu_adapter_process_failure_contains_step_context(tmp_path, monkeypatch):
    settings, _ = _build_shiyu_root(tmp_path)
    adapter = ShiyuGrddc2022Adapter(settings=settings)
    input_image = tmp_path / "road.png"
    input_image.write_bytes(VALID_IMAGE_BYTES)

    class _FailingOnY5Process:
        def __init__(self, command, *args, **kwargs):
            _ = (args, kwargs)
            self.command = command
            if "yolov5" in " ".join(command):
                self.returncode = 2
            else:
                self.returncode = 0

        def communicate(self, timeout=None):
            _ = timeout
            if "yolov7" in " ".join(self.command):
                project = Path(self.command[self.command.index("--project") + 1])
                name = self.command[self.command.index("--name") + 1]
                filename = self.command[self.command.index("--filename") + 1]
                out = project / name / filename
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text("road.jpg,1 1 2 3 4\n", encoding="utf-8")
                return "ok", ""
            if "yolov5" in " ".join(self.command):
                return "", "boom from y5"
            return "ok", ""

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = 1

        def wait(self, timeout=None):
            _ = timeout
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(subprocess, "Popen", _FailingOnY5Process)

    model = next(item for item in adapter.list_models() if item.model_id == "shiyu-cpu-ensemble-default")
    with pytest.raises(AdapterExecutionError) as exc_info:
        adapter.run(str(input_image), str(tmp_path / "workspace"), model)

    assert exc_info.value.code == "ENGINE_RUNTIME_ERROR"
    assert "[yolov5_detect]" in exc_info.value.message


def test_shiyu_adapter_falls_back_when_pillow_missing(tmp_path, monkeypatch):
    settings, _ = _build_shiyu_root(tmp_path)
    adapter = ShiyuGrddc2022Adapter(settings=settings)
    input_image = tmp_path / "road.png"
    input_image.write_bytes(VALID_IMAGE_BYTES)
    output_image = tmp_path / "annotated.png"

    real_import = builtins.__import__

    def _import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError("mock missing pillow")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _import)

    adapter._render_annotated_image(
        source_image_path=input_image,
        detections=[{"label": "D00", "confidence": None, "bbox": {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0}}],
        output_path=output_image,
    )

    assert output_image.exists()
    assert output_image.read_bytes() == input_image.read_bytes()
