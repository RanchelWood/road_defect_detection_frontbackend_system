# Frontend (React + TypeScript)

This frontend now includes Milestone 2 MVP flows:

- `/login` and `/register` wired to backend auth APIs
- Protected `/dashboard` with health check + logout
- Protected `/inference` page with:
  - model loading
  - image upload + job submission
  - async polling (`queued/running` -> terminal)
  - result metadata + detections rendering
  - authenticated annotated image fetching
- Protected `/history` page with pagination/filtering and deep-link reopen of prior jobs
- Auth state persisted in local storage with 401 session-clear redirect handling

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
