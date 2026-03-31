# MVP Bug Tracker

Lightweight Team Leader tracking table for verification-gated bug flow.

| bug_id | title | severity | area | owner | status | updated_at |
| --- | --- | --- | --- | --- | --- | --- |
| BUG-20260322-001 | Inference page required manual refresh to show terminal state | high | frontend | Frontend Engineer (`@Anscombe`) + Team Leader direct follow-up | closed | 2026-03-23 (retest confirmed) |
| BUG-20260322-002 | Elapsed timer format and anchor behavior inconsistent (`480:00` / refresh reset) | low | frontend | Frontend Engineer (`@Anscombe`) + Team Leader direct follow-up | closed | 2026-03-23 (retest confirmed) |
| BUG-20260322-003 | Annotated result image not reliably rendered from inference result | medium | integration | Backend Engineer (`@Ptolemy`) + Frontend Engineer (`@Anscombe`) | closed | 2026-03-23 00:19 +08 |
| BUG-20260325-001 | Selected model reset to first option after manual refresh | medium | frontend | Frontend Engineer (`@Anscombe`) | closed | 2026-03-25 (verified) |
| BUG-20260325-002 | User could not cancel queued/running inference jobs | high | integration | Backend Engineer (`@Ptolemy`) + Frontend Engineer (`@Anscombe`) | closed | 2026-03-25 (verified) |
| BUG-20260325-003 | History lacked sorting controls and ordering contract | medium | integration | Backend Engineer (`@Ptolemy`) + Frontend Engineer (`@Anscombe`) | closed | 2026-03-25 (verified) |
| BUG-20260326-001 | ORDDC Phase1/Phase2 jobs failed with `ENGINE_RUNTIME_ERROR` due relative runtime paths and non-actionable truncated error text | high | backend | Backend Engineer (`@Ptolemy`) | closed | 2026-03-26 (phase1+phase2 retest passed) |
| BUG-20260328-003 | Milestone 3E backend adapter pytest verification blocked by `WinError 5` tmp-dir permission in Codex sandbox | high | integration | Team Leader review (environment blocker) | closed | 2026-03-31 (outside-sandbox retest passed: `6 passed`) |
| BUG-20260328-004 | Frontend Vitest/Playwright startup blocked by `EPERM lstat C:\Users\18926` in Codex sandbox | high | integration | Team Leader review (environment blocker) | closed | 2026-03-31 (outside-sandbox retest passed: `1 file, 6 tests`) |
| BUG-20260328-005 | ShiYu presets failed with `ENGINE_NOT_RUNNABLE` / traced-model runtime failure causing missing annotated overlays | high | backend | Team Leader direct fix + Backend Engineer (`@Ptolemy`) patch | closed | 2026-03-31 (runtime retest passed) |

## Notes

- `BUG-20260322-001/002` were reopened after initial closure and resolved again in a direct Team Leader patch cycle (timezone-safe timestamp parsing, explicit UTC serialization, non-overlapping polling).
- 2026-03-25 UI enhancement requests (history card filename/model display and theme toggle) were delivered as feature work, not tracked as defects.
- `BUG-20260326-001` root cause was adapter command paths passed as relative ORDDC script inputs; fix switched ORDDC command args to absolute paths and improved traceback-tail error reporting.
- `BUG-20260328-003/004` closure evidence (2026-03-31): Team Leader applied focused test-suite fixes (ShiYu missing-weights adapter test stub + stale frontend assertion alignment), then Test Engineer reran both suites outside sandbox restrictions and confirmed pass (`backend: 6 passed`, `frontend: 1 file / 6 tests passed`).
- `BUG-20260328-005` closure evidence (2026-03-31): Test Engineer reran live API flow for both ShiYu presets, confirmed terminal `succeeded`, verified annotated artifacts differ from original (overlay present), and captured runtime logs showing YOLOv7 `--no-trace` (`no_trace=True`).
- All closed issues followed verification-gated closure: `triaged -> in progress -> fixed -> needs retest -> closed`.
