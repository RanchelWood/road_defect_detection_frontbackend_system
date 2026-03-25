import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from app.core.config import Settings, get_settings
from app.services.adapters.base import (
    AdapterExecutionError,
    AdapterExecutionResult,
    InferenceEngineAdapter,
    ModelPreset,
)


class Rddc2020Adapter(InferenceEngineAdapter):
    _LABEL_MAP = {
        "1": "D00",
        "2": "D10",
        "3": "D20",
        "4": "D40",
    }

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

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
                weights=("weights/IMSC/last_95.pt",),
                conf_thres=0.20,
                iou_thres=0.9999,
            ),
            ModelPreset(
                model_id="rddc2020-imsc-ensemble-test1",
                engine_id=self.engine_id,
                display_name="RDDC2020 IMSC Ensemble Test1",
                description="Ensemble preset tuned for road2020 test1-style images.",
                performance_notes="Higher accuracy, slower runtime due to multiple weights.",
                weights=(
                    "weights/IMSC/last_95_448_32_aug2.pt",
                    "weights/IMSC/last_95_640_16.pt",
                    "weights/IMSC/last_120_640_32_aug2.pt",
                ),
                conf_thres=0.22,
                iou_thres=0.9999,
            ),
            ModelPreset(
                model_id="rddc2020-imsc-ensemble-test2",
                engine_id=self.engine_id,
                display_name="RDDC2020 IMSC Ensemble Test2",
                description="Ensemble preset tuned for road2020 test2-style images.",
                performance_notes="Higher accuracy, slower runtime due to multiple weights.",
                weights=(
                    "weights/IMSC/last_95_448_32_aug2.pt",
                    "weights/IMSC/last_95_640_16.pt",
                    "weights/IMSC/last_120_640_32_aug2.pt",
                    "weights/IMSC/last_100_100_640_16.pt",
                ),
                conf_thres=0.22,
                iou_thres=0.9999,
            ),
        ]

    def run(
        self,
        input_image_path: str,
        job_workspace: str,
        model: ModelPreset,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AdapterExecutionResult:
        python_exe = Path(self._settings.rddc2020_python_path)
        yolov5_root = Path(self._settings.rddc2020_yolov5_root)
        detect_script = yolov5_root / "detect.py"

        if not python_exe.exists():
            raise AdapterExecutionError(
                "ENGINE_NOT_RUNNABLE",
                f"Configured rddc2020 python executable is missing: {python_exe}",
            )

        if not detect_script.exists():
            raise AdapterExecutionError(
                "ENGINE_NOT_RUNNABLE",
                f"Configured detect.py is missing: {detect_script}",
            )

        workspace = Path(job_workspace)
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)

        output_dir = workspace / "output"
        csv_path = workspace / "results.csv"
        source_path = Path(input_image_path).resolve()

        if not source_path.exists():
            raise AdapterExecutionError(
                "INPUT_MISSING",
                f"Input file does not exist: {source_path}",
            )

        weights: list[str] = []
        for relative_weight in model.weights:
            absolute_weight = (yolov5_root / relative_weight).resolve()
            if not absolute_weight.exists():
                raise AdapterExecutionError(
                    "WEIGHTS_MISSING",
                    f"Weight file not found: {absolute_weight}",
                )
            weights.append(str(absolute_weight))

        argv = [
            "detect.py",
            "--weights",
            *weights,
            "--img-size",
            str(model.img_size),
            "--source",
            str(source_path),
            "--output",
            str(output_dir.resolve()),
            "--conf-thres",
            f"{model.conf_thres:.4f}",
            "--iou-thres",
            f"{model.iou_thres:.4f}",
            "--device",
            self._settings.rddc2020_device,
        ]

        if model.agnostic_nms:
            argv.append("--agnostic-nms")
        if model.augment:
            argv.append("--augment")

        wrapper_script = self._build_wrapper_script(argv=argv, csv_path=str(csv_path.resolve()))

        started = time.time()
        process = subprocess.Popen(
            [str(python_exe), "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(yolov5_root),
        )

        stdout_text, stderr_text = self._communicate_with_cancellation(
            process=process,
            wrapper_script=wrapper_script,
            cancel_requested=cancel_requested,
        )

        duration_ms = int((time.time() - started) * 1000)

        if process.returncode != 0:
            error_text = stderr_text.strip() or stdout_text.strip()
            if len(error_text) > 1200:
                error_text = error_text[:1200]
            raise AdapterExecutionError(
                "ENGINE_RUNTIME_ERROR",
                error_text or "rddc2020 process exited with a non-zero status.",
            )

        annotated_image = output_dir / source_path.name
        if not annotated_image.exists():
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"Annotated image was not produced at expected path: {annotated_image}",
            )

        detections = self._parse_csv(csv_path=csv_path, target_filename=source_path.name)

        return AdapterExecutionResult(
            annotated_image_path=str(annotated_image.resolve()),
            detections=detections,
            duration_ms=duration_ms,
        )

    def _communicate_with_cancellation(
        self,
        process: subprocess.Popen[str],
        wrapper_script: str,
        cancel_requested: Callable[[], bool] | None,
    ) -> tuple[str, str]:
        timeout_seconds = self._settings.rddc2020_timeout_seconds
        started = time.time()
        input_payload: str | None = wrapper_script

        while True:
            elapsed = time.time() - started
            remaining = timeout_seconds - elapsed
            if remaining <= 0:
                self._terminate_process(process)
                raise AdapterExecutionError(
                    "ENGINE_TIMEOUT",
                    f"rddc2020 inference exceeded timeout of {timeout_seconds}s",
                )

            try:
                return process.communicate(input=input_payload, timeout=min(0.5, remaining))
            except subprocess.TimeoutExpired:
                input_payload = None
                if cancel_requested is not None and cancel_requested():
                    self._terminate_process(process)
                    raise AdapterExecutionError("JOB_CANCELLED", "Inference job was cancelled.")

    def _terminate_process(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return

        process.terminate()
        try:
            process.wait(timeout=2)
            return
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

    def _parse_csv(self, csv_path: Path, target_filename: str) -> list[dict[str, object]]:
        if not csv_path.exists():
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"Expected CSV output is missing: {csv_path}",
            )

        detections: list[dict[str, object]] = []
        with csv_path.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line:
                    continue

                filename, _, payload = line.partition(",")
                if filename != target_filename:
                    continue

                tokens = payload.strip().split()
                for index in range(0, len(tokens), 5):
                    if index + 4 >= len(tokens):
                        break

                    class_id = tokens[index]
                    try:
                        x1 = int(tokens[index + 1])
                        y1 = int(tokens[index + 2])
                        x2 = int(tokens[index + 3])
                        y2 = int(tokens[index + 4])
                    except ValueError as exc:
                        raise AdapterExecutionError(
                            "ENGINE_OUTPUT_PARSE_ERROR",
                            f"Failed parsing CSV detection values: {exc}",
                        ) from exc

                    detections.append(
                        {
                            "label": self._LABEL_MAP.get(class_id, f"class_{class_id}"),
                            "confidence": None,
                            "bbox": {
                                "x1": x1,
                                "y1": y1,
                                "x2": x2,
                                "y2": y2,
                            },
                        }
                    )

                break

        return detections

    def _build_wrapper_script(self, argv: list[str], csv_path: str) -> str:
        return f"""
import builtins
import runpy
import sys
import torch

ARGV = {argv!r}
CSV_TARGET = {csv_path!r}

orig_load = torch.load

def patched_load(*args, **kwargs):
    kwargs.pop('weights_only', None)
    return orig_load(*args, **kwargs)

torch.load = patched_load

orig_open = builtins.open

def patched_open(file, mode='r', *args, **kwargs):
    if file == 'results.csv' and ('w' in mode or 'a' in mode):
        return orig_open(CSV_TARGET, mode, *args, **kwargs)
    return orig_open(file, mode, *args, **kwargs)

builtins.open = patched_open

sys.argv = ARGV
runpy.run_path('detect.py', run_name='__main__')
"""
