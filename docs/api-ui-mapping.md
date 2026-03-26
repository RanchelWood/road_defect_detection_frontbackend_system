# API to UI Mapping Matrix

This matrix ties each UI screen to backend endpoints and expected response states.

## Implemented MVP Screens

| Screen | Endpoint(s) | Loading State | Success State | Error State | Empty State |
|---|---|---|---|---|---|
| Login | `POST /auth/login` | Disable form and show spinner | Persist token and redirect dashboard | Show credential error message | N/A |
| Register | `POST /auth/register` | Disable form and show spinner | Route to dashboard after auth payload | Show validation field errors | N/A |
| Dashboard | `GET /models` | Skeleton cards | Actions enabled | Non-blocking alert | If models unavailable, fallback message |
| Image Inference Submit | `GET /models`, `POST /inference/jobs` | Disable submit and show queue state | Show `job_id` and start polling | Show API error with retry | Before first run show upload prompt |
| Image Inference Poll | `GET /inference/jobs/{job_id}` (polling) | Show `queued/running` status indicator + elapsed timer | Render annotated image + detections on `succeeded`; show cancel-complete state on `cancelled` | Show failure state on `failed` | N/A |
| Image Inference Cancel | `POST /inference/jobs/{job_id}/cancel` | Disable cancel button and show `Cancelling...` | Status transitions to `cancelled` and polling stops | Show API error and keep current status | N/A |
| History list + filters/sorting | `GET /history` | Card/list skeleton | Render job list with statuses and details (title from `original_filename`) | Show retry alert | Show no-history illustration |
| History delete one | `DELETE /history/{job_id}` + follow-up `GET /history` | Disable delete buttons and show deleting state | Item removed and totals/pagination refreshed | Show API error message and keep list stable | If last item deleted, empty state appears |
| History clear all | `DELETE /history` + follow-up `GET /history` | Disable actions and show clearing state | All user history removed; page resets safely | Show API error message and keep list stable | Empty state shown with CTA |
| History page size | `GET /history?page_size=10|20|50` | Disable controls during refresh | List count and pagination update to selected size | Show API error and preserve safe defaults | N/A |

## Planned Video Screens (Not Implemented Yet)

| Screen | Endpoint(s) | Loading State | Success State | Error State | Empty State |
|---|---|---|---|---|---|
| Video Inference Submit | `GET /models`, `POST /inference/video/jobs` | Disable submit and show upload/validation progress | Show `job_id` and route to video-job detail | Show validated upload/model error | Show upload prompt |
| Video Inference Poll | `GET /inference/video/jobs/{job_id}` (polling) | Show `queued/preparing_frames/running/rendering` | Show summary stats + preview artifacts on `succeeded`; show cancel-complete state on `cancelled` | Show failure card and retry guidance | N/A |
| Video Inference Cancel | `POST /inference/video/jobs/{job_id}/cancel` | Disable cancel button and show `Cancelling...` | Status becomes `cancelled` and polling stops | Show API error and keep current status | N/A |
| Planned Streaming Page (Phase 4B) | `GET /ws/inference` | Show websocket connecting state | Show live frame overlays and latency | Show reconnect prompt + error detail | N/A |

## UI State Contract Rules

- All network failures must map to standard API error envelope fields (`code`, `message`, `request_id`).
- Unauthorized responses (`401`) must clear auth state and redirect to login.
- Job polling must stop when terminal status (`succeeded`, `failed`, or `cancelled`) is reached.
- Queued/running states must be visible to user with clear progress messaging.
- Failed jobs must show error summary and retry action.
- Cancelled jobs must show a distinct cancellation message (not generic failure).
- History page size supports exactly `10`, `20`, `50`; changing size resets to page `1`.
- History sorting supports `sort_by=time|id|name` and `sort_order=asc|desc`.
- Delete-one and clear-all are account-scoped operations only and must not affect other users.
- After delete mutations, frontend must refresh and avoid empty-page confusion by falling back to a valid page.

Planned video-specific rules:

- Video submit must validate file type/size before request send.
- Video jobs must show phase statuses (`preparing_frames`, `running`, `rendering`) distinctly.
- Phase 4B streaming must fall back to async video jobs when websocket is unavailable.
