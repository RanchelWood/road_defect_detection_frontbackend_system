# Frontend (React + TypeScript)

This frontend includes Milestone 3E MVP flows:

- `/login` and `/register` wired to backend auth APIs
- Protected `/dashboard` with health check + logout
- Light/dark theme toggle with persisted preference
- Protected `/inference` page with:
  - model loading from runtime `/models`
  - dynamic engine-family filtering derived from active engines
  - model selection persistence across refresh
  - image upload + job submission
  - async polling (`queued/running` -> terminal)
  - cancel action for queued/running jobs
  - result metadata + detections rendering (confidence hidden in UI for current engines)
  - authenticated annotated image fetching
- Protected `/history` page with pagination/filtering/sorting, delete actions, and deep-link reopen of prior jobs
- Auth state persisted in local storage with 401 session-clear redirect handling

## Local Run

From repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/login`.

Set backend URL through `VITE_API_BASE_URL` in root `.env` (default `http://localhost:8000`).

## Testing Workflow

First-time Playwright setup (one-time browser install):

```powershell
cd frontend
npm run test:e2e:install
```

Run frontend unit tests:

```powershell
cd frontend
npm run test:unit
```

Run frontend smoke E2E tests:

```powershell
cd frontend
npm run test:e2e:smoke
```

Optional:

```powershell
cd frontend
npm run test:unit:coverage
npm run test:e2e
```

## Build Check

```powershell
cd frontend
npm run build
```
