# Repository Structure – Current Snapshot

## Current State (2024-??)
- Repository is presently empty (no tracked source files or workflows).
- `.sdd/steering/` introduced in this session for specification notes.
- Upstream GitHub repository `mo666-med/line-friend-registration-system` created externally; Cursor handover package (zip) contains initial scaffolding pending import.

## Target Layout (per operating rules)
- `.github/workflows/` – GitHub Actions (manus-progress, line-event, slo-monitor, backup, etc.).
- `functions/` – Edge/Workers “Front Door” relay with signature verification and dispatch logic.
- `orchestration/` – Manus briefs, plan schemas/JSON, cost governance helpers.
- `tests/` – Unit tests for signature verification, idempotency, failure injection (403/429/timeout).
- `docs/` – Runbook, flow diagrams, SLO documentation.
- `budgets/` – Interim budget ledgers until centralized DB is adopted.
- `.cursorrules` – Cursor IDE policy file enforcing guardrails.

## Conventions & Patterns to Enforce
- TypeScript (Edge) and Python (automation) with strict lint/test gates in PR workflow.
- Shared helper to append medical safety guardrail to all outbound messages.
- Plan/PlanDelta exchanges constrained to JSON (no free-text mixing).
- Cost Governor invoked prior to Manus actions; degrade to LINE+ics path when budgets exceeded.
- Push-style progress updates via GitHub repository_dispatch webhook to Actions; ensure ProgressEvent payload conforms to v1.1 spec noted in brief.

## Debt / Follow-ups
- Need initial scaffolding for directories above and baseline configuration (lint, tests, workflows).
- Determine storage for telemetry/observability (e.g., log aggregation, Sheets audit trail).
- Document Git branching policy and PR template aligning with guardrails (Manus usage, degradation path, rationale log).
- Import prepared files from handover package or recreate via Cursor to match spec (Edge relay, workflows, cost tooling, runbook).
- Plan next execution phases outlined by prior agent (Edge deploy, Actions setup, documentation finalization) once implementation resumes.
