# Auth and Session Rules

## Authentication Method

- Email and password for registration/login.
- Passwords are stored only as bcrypt hashes.
- Access control for protected APIs via JWT bearer token.

## Token Lifecycle

- Access token lifetime: 60 minutes.
- Refresh token lifetime: 7 days.
- `POST /auth/refresh` issues a new access token.
- `POST /auth/logout` invalidates refresh token session state (implementation detail to be chosen in code stage).

## Role Stub Semantics

- Initial roles: `user` and `admin`.
- MVP behavior: both roles can use core inference and history features.
- Future behavior: `admin` reserved for model registry and operational controls.

## Password Policy (MVP)

- Minimum length: 8.
- Must include at least one letter and one number.
- Further complexity requirements can be added in future without changing auth API shape.

## Session Error Handling

- Expired/invalid token returns `401` with specific auth error code.
- Missing permission returns `403` with `AUTH_FORBIDDEN`.
- Frontend must clear session and redirect to login on `401`.