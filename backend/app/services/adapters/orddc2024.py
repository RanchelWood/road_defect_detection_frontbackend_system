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


class Orddc2024Adapter(InferenceEngineAdapter):
    _MODEL_SCRIPT_MAP = {
        "orddc2024-phase1-ensemble": "inference_script_v2_Phase1.py",
        "orddc2024-phase2-ensemble": "inference_script_v2_Phase2.py",
    }
    _MODEL_CACHE_MAP = {
        "orddc2024-phase1-ensemble": "models_ph1",
        "orddc2024-phase2-ensemble": "models_ph2",
    }

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def engine_id(self) -> str:
        return "orddc2024-cli"

    def list_models(self) -> list[ModelPreset]:
        return [
            ModelPreset(
                model_id="orddc2024-phase1-ensemble",
                engine_id=self.engine_id,
                display_name="ORDDC2024 Phase 1 Ensemble",
                description="Phase 1 ORDDC2024 ensemble preset.",
                performance_notes="Optimized for ORDDC2024 Phase 1 benchmark characteristics.",
            ),
            ModelPreset(
                model_id="orddc2024-phase2-ensemble",
                engine_id=self.engine_id,
                display_name="ORDDC2024 Phase 2 Ensemble",
                description="Phase 2 ORDDC2024 ensemble preset.",
                performance_notes="Optimized for ORDDC2024 Phase 2 benchmark characteristics.",
            ),
        ]

    def run(
        self,
        input_image_path: str,
        job_workspace: str,
        model: ModelPreset,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AdapterExecutionResult:
        python_exe = Path(self._settings.orddc2024_python_path)
        orddc_root = Path(self._settings.orddc2024_root)
        source_path = Path(input_image_path).resolve()

        if not python_exe.exists():
            raise AdapterExecutionError(
                "ENGINE_NOT_RUNNABLE",
                f"Configured orddc2024 python executable is missing: {python_exe}",
            )

        if not orddc_root.exists():
            raise AdapterExecutionError(
                "ENGINE_NOT_RUNNABLE",
                f"Configured orddc2024 root is missing: {orddc_root}",
            )

        if not source_path.exists():
            raise AdapterExecutionError(
                "INPUT_MISSING",
                f"Input file does not exist: {source_path}",
            )

        script_name = self._MODEL_SCRIPT_MAP.get(model.model_id)
        if script_name is None:
            raise AdapterExecutionError(
                "INVALID_MODEL",
                f"Model '{model.model_id}' is not supported by {self.engine_id}.",
            )

        script_path = orddc_root / script_name
        if not script_path.exists():
            raise AdapterExecutionError(
                "ENGINE_NOT_RUNNABLE",
                f"Configured ORDDC2024 script is missing: {script_path}",
            )

        cache_dir_name = self._MODEL_CACHE_MAP[model.model_id]
        cache_dir = orddc_root / cache_dir_name
        if not cache_dir.exists():
            raise AdapterExecutionError(
                "MODEL_CACHE_MISSING",
                f"Required ORDDC2024 model cache folder is missing: {cache_dir}",
            )

        workspace = Path(job_workspace)
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)

        image_root = workspace / "image_root"
        results_csv = workspace / "results.csv"
        boxed_output = workspace / "boxed_output"
        run_log = workspace / "run_log.md"

        image_root.mkdir(parents=True, exist_ok=True)
        boxed_output.mkdir(parents=True, exist_ok=True)

        image_root_abs = image_root.resolve()
        results_csv_abs = results_csv.resolve()
        boxed_output_abs = boxed_output.resolve()

        target_input = image_root / source_path.name
        shutil.copy2(source_path, target_input)

        command = [
            str(python_exe),
            str(script_path),
            str(image_root_abs),
            str(results_csv_abs),
            str(boxed_output_abs),
        ]

        started = time.time()
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(orddc_root),
        )

        stdout_text, stderr_text = self._communicate_with_cancellation(
            process=process,
            cancel_requested=cancel_requested,
        )
        duration_ms = int((time.time() - started) * 1000)

        self._write_run_log(
            run_log_path=run_log,
            command=command,
            return_code=process.returncode,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
        )

        if process.returncode != 0:
            error_text = self._build_runtime_error_summary(stdout_text=stdout_text, stderr_text=stderr_text)
            raise AdapterExecutionError(
                "ENGINE_RUNTIME_ERROR",
                error_text or "orddc2024 process exited with a non-zero status.",
            )

        if not results_csv_abs.exists() or results_csv_abs.stat().st_size == 0:
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"Expected non-empty CSV output is missing: {results_csv_abs}",
            )

        annotated_image = boxed_output_abs / source_path.name
        if not annotated_image.exists():
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"Boxed output image is missing: {annotated_image}",
            )

        detections = self._parse_csv(results_csv=results_csv_abs, target_filename=source_path.name)

        return AdapterExecutionResult(
            annotated_image_path=str(annotated_image.resolve()),
            detections=detections,
            duration_ms=duration_ms,
        )

    def _communicate_with_cancellation(
        self,
        process: subprocess.Popen[str],
        cancel_requested: Callable[[], bool] | None,
    ) -> tuple[str, str]:
        timeout_seconds = self._settings.orddc2024_timeout_seconds
        started = time.time()

        while True:
            elapsed = time.time() - started
            remaining = timeout_seconds - elapsed
            if remaining <= 0:
                self._terminate_process(process)
                raise AdapterExecutionError(
                    "ENGINE_TIMEOUT",
                    f"orddc2024 inference exceeded timeout of {timeout_seconds}s",
                )

            try:
                return process.communicate(timeout=min(0.5, remaining))
            except subprocess.TimeoutExpired:
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

    def _parse_csv(self, results_csv: Path, target_filename: str) -> list[dict[str, object]]:
        detections: list[dict[str, object]] = []
        with results_csv.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line:
                    continue

                filename, separator, payload = line.partition(",")
                if not separator:
                    continue
                if Path(filename).name != target_filename:
                    continue

                tokens = payload.strip().split()
                for index in range(0, len(tokens), 5):
                    if index + 4 >= len(tokens):
                        break

                    label = tokens[index]
                    try:
                        x1 = float(tokens[index + 1])
                        y1 = float(tokens[index + 2])
                        x2 = float(tokens[index + 3])
                        y2 = float(tokens[index + 4])
                    except ValueError as exc:
                        raise AdapterExecutionError(
                            "ENGINE_OUTPUT_PARSE_ERROR",
                            f"Failed parsing CSV detection values: {exc}",
                        ) from exc

                    detections.append(
                        {
                            "label": label,
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

    def _write_run_log(
        self,
        run_log_path: Path,
        command: list[str],
        return_code: int | None,
        stdout_text: str,
        stderr_text: str,
    ) -> None:
        log = [
            "# ORDDC2024 Run Log",
            "",
            f"Return code: {return_code}",
            f"Command: {' '.join(command)}",
            "",
            "## STDOUT",
            "```",
            stdout_text.strip(),
            "```",
            "",
            "## STDERR",
            "```",
            stderr_text.strip(),
            "```",
            "",
        ]
        run_log_path.write_text("\n".join(log), encoding="utf-8")

    def _build_runtime_error_summary(self, stdout_text: str, stderr_text: str) -> str:
        limit = 1200
        stderr_clean = stderr_text.strip()
        stdout_clean = stdout_text.strip()

        if stderr_clean:
            base = stderr_clean
        elif stdout_clean:
            base = stdout_clean
        else:
            return ""

        traceback_index = base.rfind("Traceback")
        if traceback_index >= 0:
            base = base[traceback_index:]

        if len(base) <= limit:
            return base
        return base[-limit:]
