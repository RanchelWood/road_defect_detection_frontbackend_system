# Parallel Workstream Ownership Plan

This document defines parallel ownership for Milestone 2 external integration and current QA hardening.

## Thread Structure (Workflow Governance)

- Team Leader
  - Frontend Engineer
  - Backend Engineer
  - Test Engineer
  - Junior developer guidance and repository walkthrough support

Role split reminder:

- Team Leader supervises triage, ownership, and closure readiness.
- Test Engineer executes required test suites and provides evidence.

## Workstream A: Product and UX

Ownership:

- `docs/ux-wireframes-and-flows.md`
- `docs/api-ui-mapping.md`
- UI acceptance updates in `plans/execplan-road-damage-system-mvp.md`

Deliverables:

- Job-based UX (`queued/running/succeeded/failed`).
- Polling and failure recovery interaction rules.

## Workstream B: Backend Contracts and Data

Ownership:

- `docs/contracts/openapi.yaml`
- `docs/contracts/model-registry.md`
- `docs/contracts/error-envelope.md`
- `docs/architecture/data-model.md`

Deliverables:

- Stable async jobs API.
- Multi-engine model/engine contract and schema alignment.

## Workstream C: Inference Engine Integration (First Engine)

Ownership:

- `plans/execplan-road-damage-system-mvp.md` Milestone 2B/2C details
- engine integration design notes and operational assumptions

Deliverables:

- `rddc2020-cli` adapter plan.
- Per-job working/output isolation plan.
- Output parsing normalization contract.

## Workstream D: Infra and Operations

Ownership:

- `docs/operations/runbook.md`
- `docs/operations/migration-paths.md`
- `infra` runtime topology planning updates

Deliverables:

- Runtime isolation runbook.
- Backup and cleanup strategy for job artifacts.
- Migration path to multi-engine runtime model.

## Workstream E: QA and Integration Governance

Ownership:

- `docs/engineering/workflow-and-quality-gates.md`
- `docs/engineering/test-engineer-workflow.md`
- validation sections in ExecPlan

Deliverables:

- Adapter and lifecycle test matrix.
- Concurrency and failure-mode checklist.
- Bug lifecycle governance (`new -> triaged -> in progress -> fixed -> needs retest -> closed`).
- Decision-log consolidation in living ExecPlan.

## Workstream F: Bug Discovery, Test Execution, and Verification

Ownership:

- Test Engineer thread operations
- bug report templates and assignment/retest templates in workflow docs
- release-candidate smoke regression evidence

Deliverables:

- Reproducible bug reports with severity, area classification, and suspected owner.
- Executed test-command evidence for each bug and retest cycle.
- Retest outcomes for every fixed issue before closure.
- Escalation list for integration or unclear ownership defects.
- Active frontend QA automation deliverables:
  - Vitest `v4.1.0` unit/component regression pack
  - Playwright `v1.58.2` browser smoke/retest pack with trace artifacts
