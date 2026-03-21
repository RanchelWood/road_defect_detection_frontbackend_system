# Road Damage Defect System

This repository now contains the full preparation package for implementing a YOLO-based road defect web system.

Current status: preparation artifacts are complete; feature code implementation is the next phase guided by the living ExecPlan.

## Core Planning Artifacts

- `plans/execplan-road-damage-system-mvp.md`: canonical living ExecPlan aligned with `plans/PLANS.md`
- `docs/mvp-scope.md`: MVP boundary (in scope, out of scope, phase 2)
- `docs/ux-wireframes-and-flows.md`: low-fidelity frontend wireframes and user flows
- `docs/api-ui-mapping.md`: screen-to-endpoint mapping with UI states

## Contracts and Data Model

- `docs/contracts/openapi.yaml`: initial API contract
- `docs/contracts/error-envelope.md`: standard error format
- `docs/contracts/auth-session-rules.md`: auth lifecycle and role stub behavior
- `docs/contracts/model-registry.md`: model selection and validation contract
- `docs/contracts/realtime-websocket-contract.md`: reserved phase 2 streaming contract
- `docs/architecture/data-model.md`: entities and relationships

## Engineering and Ops

- `docs/engineering/workflow-and-quality-gates.md`: setup, tests, quality bar
- `docs/engineering/parallel-workstreams.md`: ownership model for parallel implementation
- `docs/operations/runbook.md`: single-VM Docker runbook and observability baseline
- `docs/operations/migration-paths.md`: upgrade paths (DB, storage, runtime, service split)
- `infra/docker-compose.yml`: initial deployment template
- `.env.example`: environment variable template

## Scaffold Directories

- `frontend/README.md`: frontend implementation shape and stack
- `backend/README.md`: backend implementation shape and stack

## Next Step

Start implementation directly from `plans/execplan-road-damage-system-mvp.md` Milestone 1 and keep the living sections updated at every stop point.