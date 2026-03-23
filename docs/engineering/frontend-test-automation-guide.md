# Frontend Test Automation Guide (Beginner-Friendly)

This guide explains how to use the new Vitest + Playwright workflow in this repo.

## Why We Added This

The MVP already works, but we need fast and repeatable checks to catch regressions:

- Vitest: quick checks for frontend logic and API-client behavior.
- Playwright: real browser checks for user flows (login, protected routes, inference flow).

## Current Tool Versions in This Repo

- Vitest: `4.1.0`
- Playwright: `1.58.2`
- jsdom: `24.1.3` (compatibility pin for this environment)

## One-Time Setup

```powershell
cd frontend
npm install
npm run test:e2e:install
```

## Daily Commands

Run unit tests (fast):

```powershell
cd frontend
npm run test:unit
```

Run smoke E2E tests (critical user flows):

```powershell
cd frontend
npm run test:e2e:smoke
```

Run production build check:

```powershell
cd frontend
npm run build
```

## Recommended Developer Workflow

1. Make your frontend change.
2. Run `npm run test:unit`.
3. If your change touches auth/navigation/inference/history flow, run `npm run test:e2e:smoke`.
4. Run `npm run build` before handoff.
5. If any command fails, fix and rerun before reporting done.

## What Is Covered Right Now

### Vitest

- `src/utils/time.test.ts`
  - UTC normalization for server timestamps
  - elapsed timer formatting (`mm:ss`)
- `src/api/client.test.ts`
  - JSON request behavior
  - 401 unauthorized callback behavior
  - blob endpoint error-envelope handling

### Playwright Smoke

- `tests/e2e/smoke.spec.ts`
  - unauthenticated protected-route redirect
  - login -> dashboard -> logout
  - inference submit -> polling -> succeeded result render

## How Test Results Should Be Used in Team Workflow

- Unit test fail: usually frontend ownership first.
- Smoke test fail:
  - could be frontend, backend, or integration.
  - Team Leader triages and assigns owner.
- Bug is not closed until Test Engineer retest passes.

## Evidence to Attach for Bug Reports

- Command run (`test:unit` or `test:e2e:smoke`)
- Failing test name
- Error message snippet
- For Playwright: trace/video/screenshot path if generated

Use the existing bug-report template in:

- `docs/engineering/test-engineer-workflow.md`

## Common Issues and Fixes

### "Executable doesn't exist" in Playwright

Cause: browser binary not installed.

Fix:

```powershell
cd frontend
npm run test:e2e:install
```

### Vitest environment/dependency startup errors

Cause: environment compatibility mismatch.

Fix: keep repo-pinned versions (Vitest 4.1.0 + jsdom 24.1.3), then reinstall:

```powershell
cd frontend
npm install
npm run test:unit
```

