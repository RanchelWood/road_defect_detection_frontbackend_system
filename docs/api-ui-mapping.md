# API to UI Mapping Matrix

This matrix ties each UI screen to backend endpoints and expected response states.

| Screen | Endpoint(s) | Loading State | Success State | Error State | Empty State |
|---|---|---|---|---|---|
| Login | `POST /auth/login` | Disable form and show spinner | Persist token and redirect dashboard | Show credential error message | N/A |
| Register | `POST /auth/register` | Disable form and show spinner | Show success toast then route to login | Show validation field errors | N/A |
| Dashboard | `GET /models` (optional prefetch) | Skeleton cards | Actions enabled | Non-blocking alert | If models unavailable, fallback message |
| Image Inference | `GET /models`, `POST /inference/image` | Disable run button and show progress | Render annotated image and detections list | Show API error with retry button | Before first run show upload prompt |
| History | `GET /history` | Table skeleton | Render rows with detail action | Show retry alert | Show no-history illustration |
| Result Detail (optional) | `GET /inference/{id}` | Spinner in detail panel | Render full inference detail | Show not found or unauthorized | N/A |

## UI State Contract Rules

- All network failures must map to standard API error envelope fields (`code`, `message`, `request_id`).
- Form validation errors must highlight fields and include backend error detail when available.
- Unauthorized responses (`401`) must clear auth state and redirect to login.
- Forbidden responses (`403`) must preserve session and show permissions message.
- Any long-running request over 1 second should show explicit loading feedback.