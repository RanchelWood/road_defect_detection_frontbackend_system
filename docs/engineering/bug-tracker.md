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

## Notes

- `BUG-20260322-001/002` were reopened after initial closure and resolved again in a direct Team Leader patch cycle (timezone-safe timestamp parsing, explicit UTC serialization, non-overlapping polling).
- 2026-03-25 UI enhancement requests (history card filename/model display and theme toggle) were delivered as feature work, not tracked as defects.
- All listed issues followed verification-gated closure: `triaged -> in progress -> fixed -> needs retest -> closed`.
- Verification evidence was provided by Test Engineer before closure.
