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
| BUG-20260328-003 | Milestone 3E backend adapter pytest verification blocked by `WinError 5` tmp-dir permission in Codex sandbox | high | integration | Team Leader review (environment blocker) | triaged | 2026-03-28 |
| BUG-20260328-004 | Frontend Vitest/Playwright startup blocked by `EPERM lstat C:\Users\18926` in Codex sandbox | high | integration | Team Leader review (environment blocker) | triaged | 2026-03-28 |
| BUG-20260328-005 | ShiYu presets failed with `ENGINE_NOT_RUNNABLE` when Pillow missing for annotated render | high | backend | Team Leader direct fix | needs retest | 2026-03-28 |

## Notes

- `BUG-20260322-001/002` were reopened after initial closure and resolved again in a direct Team Leader patch cycle (timezone-safe timestamp parsing, explicit UTC serialization, non-overlapping polling).
- 2026-03-25 UI enhancement requests (history card filename/model display and theme toggle) were delivered as feature work, not tracked as defects.
- `BUG-20260326-001` root cause was adapter command paths passed as relative ORDDC script inputs; fix switched ORDDC command args to absolute paths and improved traceback-tail error reporting.
- `BUG-20260328-003/004` are environment blockers for in-sandbox verification and require local-host rerun evidence for closure.
- `BUG-20260328-005` fix keeps ShiYu jobs runnable without Pillow by falling back to copied annotated image; close only after user-side retest confirms expected behavior.
- All closed issues followed verification-gated closure: `triaged -> in progress -> fixed -> needs retest -> closed`.
