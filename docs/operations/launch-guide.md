# Launch Guide

This guide shows the simplest way to start the Road Damage Defect System on a Windows machine with PowerShell.

The project currently has two app services plus one inference runtime dependency:
- Backend: FastAPI on `http://localhost:8000`
- Frontend: React on `http://localhost:5173`
- External inference runtime: sibling `rddc2020` path used by backend adapter for image jobs

Planned next runtime integration: `orddc2024` (not enabled yet in current code).

## First-Time Setup

Run these steps only once, or again if you delete your local environment folders.

1. Open PowerShell and go to the repository root.

    cd D:\road_defect_detection\frondend-backend-system

2. Create the environment file if it does not exist yet.

    copy .env.example .env

3. Start the backend dependency environment.

    cd backend
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt

4. Start the frontend dependency install.

    cd ..\frontend
    npm install

5. Confirm external runtime prerequisites for inference.

    - `D:\road_defect_detection\rddc2020` exists.
    - Required model weight files are present under `rddc2020\yolov5\weights\IMSC`.
    - The runtime can execute inference command in its own environment.

## Every Time You Want to Run the Project

Use two PowerShell windows. Keep one for the backend and one for the frontend.

### Window 1: Backend

1. Go to the backend folder.

    cd D:\road_defect_detection\frondend-backend-system\backend

2. Activate the virtual environment.

    .\.venv\Scripts\activate

3. Start the backend server.

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

What you should see:
- Uvicorn startup messages
- The server stays running
- The backend is available at `http://localhost:8000`

### Window 2: Frontend

1. Go to the frontend folder.

    cd D:\road_defect_detection\frondend-backend-system\frontend

2. Start the frontend dev server.

    npm run dev

What you should see:
- Vite startup messages
- The frontend is available at `http://localhost:5173`

## What To Open In The Browser

After both servers are running, open:

- `http://localhost:5173/login`

From there you can:
- Register a new account
- Log in
- Open the dashboard
- Check backend health
- Open inference and history pages
- Switch light/dark theme

## Simple Verification Checklist

1. Log in successfully.
2. Open the dashboard.
3. Click `Check /health` and confirm the status becomes `ok`.
4. Open `Inference`.
5. Choose a model, upload an image, and submit a job.
6. Confirm the elapsed timer starts from `00:00` and increases while running.
7. (Optional) Click `Cancel job` while queued/running and confirm terminal status becomes `cancelled`.
8. For a completed job, confirm result details and annotated image rendering.
9. Open `History` and confirm the job appears with filename title and model line.
10. Change history sorting (`time|id|name`, asc/desc) and verify order changes.
11. Refresh the page and verify selected model and theme preference persist.

## Optional Docker Launch

If you have Docker Desktop installed, you can start both services with one command from the repository root:

    docker compose -f infra/docker-compose.yml up --build

Then open:
- `http://localhost:5173/login`

## Common Problems

- If the browser cannot reach the app, check whether both terminal windows are still running.
- If the backend says a port is already in use, close the old backend window and start it again.
- If `npm run dev` fails, run `npm install` again in the `frontend` folder.
- If login or job submission fails, confirm the backend is running on port `8000`.
- If jobs stay queued/running unexpectedly, confirm `rddc2020` runtime path and weights are available to backend.

## Planned Features Notice

- Async video jobs and WebSocket streaming are planned in documentation but not yet available in the current runnable build.
- See `docs/architecture/video-support-design.md` and `docs/contracts/video-inference-job-contract.md` for planned behavior.
