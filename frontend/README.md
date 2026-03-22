# Frontend (React + TypeScript)

This frontend now includes the Milestone 1 runnable scaffold with:

- `/login` page wired to backend `POST /auth/login`
- `/register` page wired to backend `POST /auth/register`
- Protected `/dashboard` page with:
  - health check button for `GET /health`
  - logout action for `POST /auth/logout`
- Auth state persisted in local storage

## Local Run

From repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open:

- `http://localhost:5173/login`

Set backend URL through `VITE_API_BASE_URL` in root `.env` (default `http://localhost:8000`).

## Build Check

```powershell
cd frontend
npm run build
```