# Test Engineer Workflow (MVP)

This document defines how the Team Leader, Frontend Engineer, Backend Engineer, and Test Engineer collaborate for bug discovery and resolution in a beginner-friendly way.

## Updated Team and Thread Structure

- Team Leader
  - Frontend Engineer (write and fix UI/frontend behavior)
  - Backend Engineer (write and fix backend/API/runtime behavior)
  - Test Engineer (run tests, discover defects, reproduce, and verify fixes)
  - Junior guidance support (Team Leader explains project and fixes in simple terms)

## Test Engineer Responsibilities

The Test Engineer is responsible for running tests from a user perspective and submitting reproducible bug reports with execution evidence.

Primary scope:

- Validate expected MVP flows:
  - register
  - login/logout
  - protected route behavior
  - image inference submission
  - model selection
  - history page behavior
  - loading/error/success states
  - API failure handling
  - 401 redirect behavior
  - deep-link and navigation behavior
- Verify user-reported issues.
- Perform exploratory checks to find new issues.
- Execute required automated suites for each report/retest scope.
- Classify issue area as one of:
  - `frontend`
  - `backend`
  - `integration`
  - `unclear`

Guardrails:

- Do not make speculative code changes unless explicitly assigned implementation work.
- Team Leader does not run routine test suites for bug closure.
- Team Leader verifies Test Engineer evidence quality and closes only after passing retest evidence.

## Automation Augmentation (Implemented)

Status on 2026-03-23: implemented in frontend workflow.

Active automation stack:

- Vitest `v4.1.0` for frontend unit/component regression checks.
- Playwright `v1.58.2` for browser-level reproduction and retest evidence.

Test Engineer expected usage:

- Run `npm run test:e2e:smoke` as fast verification for critical MVP flows.
- Attach Playwright traces/videos/screenshots when available.
- Reference related Vitest tests (`npm run test:unit`) for frontend logic regressions.
- Use manual + automated cross-check for `blocker` and `high` severity defects.

## Mandatory Test Execution Contract

For each bug report and each retest cycle, the Test Engineer must execute and report commands relevant to the affected area.

Baseline command matrix:

- Frontend-only bug:
  - `cd frontend && npm run test:unit`
  - `cd frontend && npm run test:e2e:smoke` when auth/navigation/inference/history UI is affected
- Backend-only bug:
  - `cd backend && .\.venv\Scripts\python.exe -m pytest tests`
- Integration or unclear bug:
  - `cd backend && .\.venv\Scripts\python.exe -m pytest tests`
  - `cd frontend && npm run test:unit`
  - `cd frontend && npm run test:e2e:smoke`

Minimum evidence block (required):

- Executed Commands:
  - exact command lines
- Result Summary:
  - passed/failed counts and failing test IDs
- Artifact Paths:
  - Playwright trace/video/screenshot paths when generated
- Outcome:
  - `pass` or `fail` recommendation for closure

## Bug Lifecycle

### Status Model

- `new`
- `triaged`
- `in progress`
- `fixed`
- `needs retest`
- `closed`

### Required Flow

1. Bug is reported by user or discovered by Test Engineer (`new`).
2. Team Leader reviews report, sets severity/area/owner (`triaged`).
3. Team Leader assigns bug to Frontend Engineer or Backend Engineer (`in progress`).
4. Engineer submits fix with evidence (`fixed`).
5. Team Leader sends fix to Test Engineer with retest request (`needs retest`).
6. Test Engineer verifies by executing required test commands and manual checks:
   - Pass: close issue (`closed`).
   - Fail: reopen with new evidence (`triaged`).

### Ownership Rules

- `frontend` -> Frontend Engineer
- `backend` -> Backend Engineer
- `integration` -> assign primary owner + secondary reviewer
- `unclear` -> Team Leader creates short investigation task first

### Closure Rule

- No bug is closed without Test Engineer verification evidence that includes executed commands and results.

## Standard Templates

### A) Bug Report Template (Test Engineer -> Team Leader)

```md
Bug ID: BUG-YYYYMMDD-###
Title:
Severity: blocker | high | medium | low
Area: frontend | backend | integration | unclear
Environment / Page / Route:
Preconditions:
Steps to Reproduce:
1.
2.
3.
Expected Result:
Actual Result:
Evidence / Notes:
- Manual evidence:
- Executed commands:
- Command outputs summary:
- Playwright evidence (if available): trace/video/screenshot path
- Related Vitest coverage (if available): test file/name
Suspected Owner: Frontend Engineer | Backend Engineer | Team Leader review
Suggested Next Action:
Current Status: new
Reported By:
Reported At:
```

### B) Team Leader Assignment Template (Team Leader -> Frontend/Backend Engineer)

```md
Assignment: BUG-YYYYMMDD-###
Title:
Assigned To: Frontend Engineer | Backend Engineer
Area Classification: frontend | backend | integration | unclear
Priority/Severity:
Reason for Ownership:
Reproduction Summary:
Expected vs Actual:
Scope of Fix:
Acceptance Criteria:
- Bug reproduction no longer occurs.
- No regression in related MVP flow.
- Build/tests/checks required by owner pass.
- If automation exists for scope: relevant Vitest/Playwright checks pass.
Deliverable:
- PR/patch + short fix note + risk note.
Next Status on Start: in progress
```

### C) Retest/Verification Template (Team Leader -> Test Engineer, then Test Engineer response)

```md
Retest Request: BUG-YYYYMMDD-###
Fix Reference: <commit/PR/build>
Target Environment:
Retest Focus:
Required Steps:
1.
2.
3.
Expected Retest Outcome:
Pass Criteria:
- Original bug resolved.
- Related flow still works.

Retest Result:
- Outcome: pass | fail
- Executed Commands:
- Command Output Summary:
- Manual Evidence:
- Playwright Evidence (if available):
- Related Vitest Evidence (if available):
- Residual Issues:
- Recommendation: close | re-triage
Next Status: closed (if pass) | triaged (if fail)
Verified By:
Verified At:
```

## Practical MVP Recommendations

- Keep one simple bug tracker table with columns:
  - `bug_id`, `title`, `severity`, `area`, `owner`, `status`, `updated_at`
- Limit active `in progress` bugs to a small WIP count.
- Run one short daily Team Leader triage pass.
- Require bug ID in every engineer update.
- Prefer small bug-fix batches and immediate retest handoff.
- Keep reports concrete and reproducible; avoid vague statements.
