import os
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


class ShiyuGrddc2022Adapter(InferenceEngineAdapter):
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
        return "shiyu-grddc2022-cli"

    def list_models(self) -> list[ModelPreset]:
        return [
            ModelPreset(
                model_id="shiyu-cpu-ensemble-default",
                engine_id=self.engine_id,
                display_name="ShiYu GRDDC2022 CPU Ensemble Default",
                description="YOLOv7x_640 + YOLOv5x_640 with merge.py",
                performance_notes="CPU-safe phased rollout default preset.",
            ),
            ModelPreset(
                model_id="shiyu-yolov7x-640",
                engine_id=self.engine_id,
                display_name="ShiYu GRDDC2022 YOLOv7x 640",
                description="Single YOLOv7x_640 fallback preset.",
                performance_notes="Single-model fallback for faster rollout and diagnostics.",
            ),
            ModelPreset(
                model_id="shiyu-y7x640-faster-swin-w7",
                engine_id=self.engine_id,
                display_name="ShiYu GRDDC2022 Y7x640 + Faster-Swin-W7",
                description="Demo preset: YOLOv7x_640 first-stage + Faster-Swin-L W7 second-stage + merge.py",
                performance_notes="Demo two-stage preset; slower on CPU than single-stage presets.",
            ),
        ]

    def run(
        self,
        input_image_path: str,
        job_workspace: str,
        model: ModelPreset,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AdapterExecutionResult:
        python_exe = Path(self._settings.shiyu_grddc2022_python_path)
        shiyu_root = Path(self._settings.shiyu_grddc2022_root)
        source_path = Path(input_image_path).resolve()

        self._ensure_file_exists(python_exe, "ENGINE_NOT_RUNNABLE", "Configured shiyu python executable is missing")
        self._ensure_dir_exists(shiyu_root, "ENGINE_NOT_RUNNABLE", "Configured shiyu root is missing")
        self._ensure_file_exists(source_path, "INPUT_MISSING", "Input file does not exist")

        workspace = Path(job_workspace)
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)

        image_root = (workspace / "image_root").resolve()
        boxed_output = (workspace / "boxed_output").resolve()
        logs_dir = (workspace / "logs").resolve()
        image_root.mkdir(parents=True, exist_ok=True)
        boxed_output.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        run_log_path = workspace / "run_log.md"
        run_log_path.write_text("# Shiyu GRDDC2022 Run Log\n\n", encoding="utf-8")

        target_input = image_root / source_path.name
        shutil.copy2(source_path, target_input)

        started = time.time()

        if model.model_id == "shiyu-cpu-ensemble-default":
            detections = self._run_ensemble(
                root=shiyu_root,
                python_exe=python_exe,
                image_root=image_root,
                logs_dir=logs_dir,
                run_log_path=run_log_path,
                target_stem=source_path.stem,
                cancel_requested=cancel_requested,
            )
        elif model.model_id == "shiyu-yolov7x-640":
            detections = self._run_single_yolov7(
                root=shiyu_root,
                python_exe=python_exe,
                image_root=image_root,
                logs_dir=logs_dir,
                run_log_path=run_log_path,
                target_stem=source_path.stem,
                cancel_requested=cancel_requested,
            )
        elif model.model_id == "shiyu-y7x640-faster-swin-w7":
            detections = self._run_y7_mmdet_merge(
                root=shiyu_root,
                python_exe=python_exe,
                image_root=image_root,
                logs_dir=logs_dir,
                run_log_path=run_log_path,
                target_stem=source_path.stem,
                cancel_requested=cancel_requested,
            )
        else:
            raise AdapterExecutionError(
                "INVALID_MODEL",
                f"Model '{model.model_id}' is not supported by {self.engine_id}.",
            )

        final_annotated = boxed_output / source_path.name
        self._render_annotated_image(
            source_image_path=target_input,
            detections=detections,
            output_path=final_annotated,
        )

        duration_ms = int((time.time() - started) * 1000)
        return AdapterExecutionResult(
            annotated_image_path=str(final_annotated),
            detections=detections,
            duration_ms=duration_ms,
        )

    def _run_ensemble(
        self,
        root: Path,
        python_exe: Path,
        image_root: Path,
        logs_dir: Path,
        run_log_path: Path,
        target_stem: str,
        cancel_requested: Callable[[], bool] | None,
    ) -> list[dict[str, object]]:
        y7_result = logs_dir / "y7_result.txt"
        y5_result = logs_dir / "y5_result.txt"
        merged_result = logs_dir / "merged_result.txt"

        self._run_yolov7_step(
            root=root,
            python_exe=python_exe,
            image_root=image_root,
            output_txt=y7_result,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )
        self._run_yolov5_step(
            root=root,
            python_exe=python_exe,
            image_root=image_root,
            output_txt=y5_result,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )

        if merged_result.exists():
            merged_result.unlink()

        merge_script = root / "merge.py"
        self._ensure_file_exists(merge_script, "ENGINE_NOT_RUNNABLE", "Missing merge.py script")

        self._run_process_step(
            step_name="merge",
            command=[
                str(python_exe.resolve()),
                str(merge_script.resolve()),
                str(y7_result.resolve()),
                str(y5_result.resolve()),
                str(merged_result.resolve()),
            ],
            cwd=root,
            timeout_seconds=self._settings.shiyu_grddc2022_timeout_seconds_ensemble,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )

        if not merged_result.exists() or merged_result.stat().st_size == 0:
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"[merge] Missing or empty merged output: {merged_result}",
            )

        return self._parse_detection_file(merged_result, target_stem)

    def _run_y7_mmdet_merge(
        self,
        root: Path,
        python_exe: Path,
        image_root: Path,
        logs_dir: Path,
        run_log_path: Path,
        target_stem: str,
        cancel_requested: Callable[[], bool] | None,
    ) -> list[dict[str, object]]:
        y7_result = logs_dir / "y7_result.txt"
        mmdet_result = logs_dir / "mmdet_result.txt"
        merged_result = logs_dir / "merged_result.txt"

        self._run_yolov7_step(
            root=root,
            python_exe=python_exe,
            image_root=image_root,
            output_txt=y7_result,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )
        self._run_mmdet_step(
            root=root,
            python_exe=python_exe,
            image_root=image_root,
            output_txt=mmdet_result,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )

        if merged_result.exists():
            merged_result.unlink()

        merge_script = root / "merge.py"
        self._ensure_file_exists(merge_script, "ENGINE_NOT_RUNNABLE", "Missing merge.py script")

        self._run_process_step(
            step_name="merge",
            command=[
                str(python_exe.resolve()),
                str(merge_script.resolve()),
                str(y7_result.resolve()),
                str(mmdet_result.resolve()),
                str(merged_result.resolve()),
            ],
            cwd=root,
            timeout_seconds=self._settings.shiyu_grddc2022_timeout_seconds_ensemble,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )

        if not merged_result.exists() or merged_result.stat().st_size == 0:
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"[merge] Missing or empty merged output: {merged_result}",
            )

        return self._parse_detection_file(merged_result, target_stem)

    def _run_single_yolov7(
        self,
        root: Path,
        python_exe: Path,
        image_root: Path,
        logs_dir: Path,
        run_log_path: Path,
        target_stem: str,
        cancel_requested: Callable[[], bool] | None,
    ) -> list[dict[str, object]]:
        y7_result = logs_dir / "y7_result.txt"
        self._run_yolov7_step(
            root=root,
            python_exe=python_exe,
            image_root=image_root,
            output_txt=y7_result,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )

        if not y7_result.exists() or y7_result.stat().st_size == 0:
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"[yolov7_detect] Missing or empty output: {y7_result}",
            )

        return self._parse_detection_file(y7_result, target_stem)

    def _run_yolov7_step(
        self,
        root: Path,
        python_exe: Path,
        image_root: Path,
        output_txt: Path,
        run_log_path: Path,
        cancel_requested: Callable[[], bool] | None,
    ) -> None:
        script = root / "yolov7" / "detect.py"
        weight = root / "yolov7" / "YOLOv7x_640.pt"
        self._ensure_file_exists(script, "ENGINE_NOT_RUNNABLE", "[yolov7_detect] Missing yolov7 detect.py")
        self._ensure_file_exists(weight, "WEIGHTS_MISSING", "[yolov7_detect] Missing yolov7 weight")

        project = output_txt.parent.resolve()
        name = "y7_run"

        self._run_process_step(
            step_name="yolov7_detect",
            command=[
                str(python_exe.resolve()),
                str(script.resolve()),
                "--weights",
                str(weight.resolve()),
                "--source",
                str(image_root.resolve()),
                "--img-size",
                "640",
                "--conf-thres",
                "0.20",
                "--iou-thres",
                "0.9999",
                "--device",
                self._settings.shiyu_grddc2022_device,
                "--agnostic-nms",
                "--no-trace",
                "--project",
                str(project),
                "--name",
                name,
                "--exist-ok",
                "--filename",
                output_txt.name,
            ],
            cwd=root,
            timeout_seconds=self._settings.shiyu_grddc2022_timeout_seconds_single,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )

        produced = project / name / output_txt.name
        if not produced.exists() or produced.stat().st_size == 0:
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"[yolov7_detect] Missing or empty output: {produced}",
            )

        shutil.copy2(produced, output_txt)

    def _run_yolov5_step(
        self,
        root: Path,
        python_exe: Path,
        image_root: Path,
        output_txt: Path,
        run_log_path: Path,
        cancel_requested: Callable[[], bool] | None,
    ) -> None:
        script = root / "yolov5" / "detect.py"
        weight = root / "yolov5" / "YOLOv5x_640.pt"
        data_yaml = root / "yolov5" / "data" / "rdd.yaml"
        self._ensure_file_exists(script, "ENGINE_NOT_RUNNABLE", "[yolov5_detect] Missing yolov5 detect.py")
        self._ensure_file_exists(weight, "WEIGHTS_MISSING", "[yolov5_detect] Missing yolov5 weight")
        self._ensure_file_exists(data_yaml, "ENGINE_NOT_RUNNABLE", "[yolov5_detect] Missing yolov5 rdd.yaml")

        project = output_txt.parent.resolve()
        name = "y5_run"

        self._run_process_step(
            step_name="yolov5_detect",
            command=[
                str(python_exe.resolve()),
                str(script.resolve()),
                "--weights",
                str(weight.resolve()),
                "--source",
                str(image_root.resolve()),
                "--data",
                str(data_yaml.resolve()),
                "--imgsz",
                "640",
                "--conf-thres",
                "0.20",
                "--iou-thres",
                "0.9999",
                "--device",
                self._settings.shiyu_grddc2022_device,
                "--agnostic-nms",
                "--project",
                str(project),
                "--name",
                name,
                "--exist-ok",
                "--filename",
                output_txt.name,
            ],
            cwd=root,
            timeout_seconds=self._settings.shiyu_grddc2022_timeout_seconds_single,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )

        produced = project / name / output_txt.name
        if not produced.exists() or produced.stat().st_size == 0:
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"[yolov5_detect] Missing or empty output: {produced}",
            )

        shutil.copy2(produced, output_txt)

    def _run_mmdet_step(
        self,
        root: Path,
        python_exe: Path,
        image_root: Path,
        output_txt: Path,
        run_log_path: Path,
        cancel_requested: Callable[[], bool] | None,
    ) -> None:
        mmdet_root = (root / "mmdetection").resolve()
        script = mmdet_root / "inference.py"

        config_value = Path(self._settings.shiyu_grddc2022_mmdet_config)
        checkpoint_value = Path(self._settings.shiyu_grddc2022_mmdet_checkpoint)

        config_path = config_value if config_value.is_absolute() else mmdet_root / config_value
        checkpoint_path = checkpoint_value if checkpoint_value.is_absolute() else mmdet_root / checkpoint_value

        self._ensure_dir_exists(mmdet_root, "ENGINE_NOT_RUNNABLE", "[mmdet_inference] Missing mmdetection directory")
        self._ensure_file_exists(script, "ENGINE_NOT_RUNNABLE", "[mmdet_inference] Missing mmdetection inference.py")
        self._ensure_file_exists(config_path, "ENGINE_NOT_RUNNABLE", "[mmdet_inference] Missing mmdetection config")
        self._ensure_file_exists(checkpoint_path, "WEIGHTS_MISSING", "[mmdet_inference] Missing mmdetection checkpoint")

        source_dir = str(image_root.resolve())
        if not source_dir.endswith("\\") and not source_dir.endswith("/"):
            source_dir = f"{source_dir}{os.sep}"

        results_dir = mmdet_root / "results_mmdet"
        results_dir.mkdir(parents=True, exist_ok=True)
        produced = results_dir / output_txt.name

        if produced.exists():
            produced.unlink()

        self._run_process_step(
            step_name="mmdet_inference",
            command=[
                str(python_exe.resolve()),
                str(script.resolve()),
                str(config_path.resolve()),
                str(checkpoint_path.resolve()),
                source_dir,
                "640",
                "0.20",
                "0.9999",
                output_txt.name,
            ],
            cwd=mmdet_root,
            timeout_seconds=self._settings.shiyu_grddc2022_timeout_seconds_mmdet,
            run_log_path=run_log_path,
            cancel_requested=cancel_requested,
        )

        if not produced.exists() or produced.stat().st_size == 0:
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_MISSING",
                f"[mmdet_inference] Missing or empty output: {produced}",
            )

        shutil.copy2(produced, output_txt)

    def _run_process_step(
        self,
        step_name: str,
        command: list[str],
        cwd: Path,
        timeout_seconds: int,
        run_log_path: Path,
        cancel_requested: Callable[[], bool] | None,
    ) -> None:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(cwd.resolve()),
        )

        stdout_text, stderr_text = self._communicate_with_cancellation(
            process=process,
            timeout_seconds=timeout_seconds,
            step_name=step_name,
            cancel_requested=cancel_requested,
        )

        self._append_run_log(
            run_log_path=run_log_path,
            step_name=step_name,
            command=command,
            return_code=process.returncode,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
        )

        if process.returncode != 0:
            details = self._tail_error(stderr_text=stderr_text, stdout_text=stdout_text)
            raise AdapterExecutionError(
                "ENGINE_RUNTIME_ERROR",
                f"[{step_name}] process failed with return code {process.returncode}. {details}",
            )

    def _communicate_with_cancellation(
        self,
        process: subprocess.Popen[str],
        timeout_seconds: int,
        step_name: str,
        cancel_requested: Callable[[], bool] | None,
    ) -> tuple[str, str]:
        started = time.time()
        while True:
            elapsed = time.time() - started
            remaining = timeout_seconds - elapsed
            if remaining <= 0:
                self._terminate_process(process)
                raise AdapterExecutionError(
                    "ENGINE_TIMEOUT",
                    f"[{step_name}] exceeded timeout of {timeout_seconds}s",
                )

            try:
                return process.communicate(timeout=min(0.5, remaining))
            except subprocess.TimeoutExpired:
                if cancel_requested is not None and cancel_requested():
                    self._terminate_process(process)
                    raise AdapterExecutionError("JOB_CANCELLED", f"[{step_name}] inference job was cancelled.")

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

    def _parse_detection_file(self, result_file: Path, target_stem: str) -> list[dict[str, object]]:
        detections: list[dict[str, object]] = []
        has_target_row = False

        with result_file.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue

                filename, sep, payload = line.partition(",")
                if not sep:
                    continue
                if Path(filename).stem != target_stem:
                    continue
                has_target_row = True

                tokens = payload.strip().split()
                for index in range(0, len(tokens), 5):
                    if index + 4 >= len(tokens):
                        break

                    class_id = tokens[index]
                    try:
                        x1 = float(tokens[index + 1])
                        y1 = float(tokens[index + 2])
                        x2 = float(tokens[index + 3])
                        y2 = float(tokens[index + 4])
                    except ValueError as exc:
                        raise AdapterExecutionError(
                            "ENGINE_OUTPUT_PARSE_ERROR",
                            f"Failed parsing detection values from {result_file}: {exc}",
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

        if not has_target_row:
            raise AdapterExecutionError(
                "ENGINE_OUTPUT_PARSE_ERROR",
                f"Missing detection row for target '{target_stem}' in {result_file}",
            )

        return detections

    def _render_annotated_image(
        self,
        source_image_path: Path,
        detections: list[dict[str, object]],
        output_path: Path,
    ) -> None:
        try:
            from PIL import Image, ImageDraw
        except ImportError:  # pragma: no cover
            # Keep inference runnable even when Pillow is absent in runtime env.
            shutil.copy2(source_image_path, output_path)
            return

        try:
            image = Image.open(source_image_path).convert("RGB")
            draw = ImageDraw.Draw(image)
            for detection in detections:
                bbox = detection.get("bbox", {})
                x1 = float(bbox.get("x1", 0.0))
                y1 = float(bbox.get("y1", 0.0))
                x2 = float(bbox.get("x2", 0.0))
                y2 = float(bbox.get("y2", 0.0))
                draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0), width=2)
                draw.text((x1 + 2, y1 + 2), str(detection.get("label", "unknown")), fill=(255, 0, 0))
            image.save(output_path)
        except Exception as exc:
            raise AdapterExecutionError(
                "ENGINE_RUNTIME_ERROR",
                f"Failed rendering final annotated image: {exc}",
            ) from exc

    def _append_run_log(
        self,
        run_log_path: Path,
        step_name: str,
        command: list[str],
        return_code: int | None,
        stdout_text: str,
        stderr_text: str,
    ) -> None:
        block = [
            f"## {step_name}",
            f"Return code: {return_code}",
            f"Command: {' '.join(command)}",
            "",
            "### STDOUT",
            "```",
            stdout_text.strip(),
            "```",
            "",
            "### STDERR",
            "```",
            stderr_text.strip(),
            "```",
            "",
        ]
        with run_log_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(block))
            handle.write("\n")

    def _tail_error(self, stderr_text: str, stdout_text: str) -> str:
        body = stderr_text.strip() or stdout_text.strip()
        if not body:
            return ""
        if len(body) <= 1200:
            return body
        return body[-1200:]

    def _ensure_file_exists(self, path: Path, code: str, message_prefix: str) -> None:
        if not path.exists() or not path.is_file():
            raise AdapterExecutionError(code, f"{message_prefix}: {path}")

    def _ensure_dir_exists(self, path: Path, code: str, message_prefix: str) -> None:
        if not path.exists() or not path.is_dir():
            raise AdapterExecutionError(code, f"{message_prefix}: {path}")

