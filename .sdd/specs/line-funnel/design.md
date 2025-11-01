# Design – Cursorvers LINE Funnel

## Scope & Context
Implements the marketing automation loop that converts note article readers into LINE subscribers, nurtures them with compliant messaging, and feeds operations through GitHub Actions while keeping Manus usage minimal. The design covers the Edge “Front Door”, GitHub Actions workflows, orchestration scripts, storage touchpoints (Google Sheets, Supabase), and supporting documentation/tests referenced in the Cursor handover package.

---

## Architecture Overview

### System Boundaries & Data Flow
```
[note article CTA] → [LINE add friend] ──┐
                                        ├─(LINE webhook, X-Line-Signature)
[Manus Progress webhook] ───────────────┘
      │
      ▼
 Front Door (Edge/Workers, TypeScript)
   - Verify signatures (LINE HMAC / Manus bearer)
   - Sanitize & hash identifiers
   - Enforce idempotency window (eventId cache)
   - Dispatch: GitHub REST `POST /dispatches`
      payload{ event_type, client_payload }
                     │
                     ▼
 GitHub Actions (YAML)
   - `line-event.yml`: plan selection, cost guard, message execution
   - `manus-progress.yml`: update state machine, log telemetry
   - Future workflows: SLO monitor, backups
                     │
                     ├─ Trigger GPT plan analysis (repository scripts)
                     ├─ Invoke Manus (fallback / last-mile)
                     ├─ Update Supabase (logs) & Google Sheets (contact ledger)
                     └─ Reply via LINE Messaging API (guardrail appended)

Progress/heartbeat events (Push)
  GitHub → `repository_dispatch` → monitoring dashboards
```

### Component Responsibilities
- **Front Door (Edge/Workers)**: 100–200 line TypeScript function running on Supabase Edge Function or Cloudflare Workers. Handles:
  - Signature verification using Node `crypto.subtle` (`HMAC-SHA256`) for LINE; bearer token comparison for Manus.
  - Payload minimisation (`sanitize` utility) removing optional fields, hashing LINE user IDs before forwarding.
  - Idempotency enforcement storing event hashes in KV (Workers KV / Supabase Key-Value or in-memory if cold start acceptable).
  - Dispatch to GitHub using PAT stored in environment secret (`GH_PAT`).

- **GitHub Actions Workflows**:
  - `line-event.yml`:
    - Parse incoming payload, detect event type (`follow`, `message`, etc.).
    - Run cost estimator (`python orchestration/cost.py`) before executing plan.
    - Choose handler (`follow` → welcome flow, `message` → command router, degrade to fallback on budget).
    - Persist subscriber metadata to Google Sheets using CLI script or Manus step (if approved).
    - Reply via LINE Messaging API (dedicated GitHub Action using OIDC + Secrets).
  - `manus-progress.yml`:
    - Receive Manus progress heartbeat/progress events.
    - Validate plan consistency, update logs, request re-run or mark success.
    - Surface outputs as artifacts or comment on PR/issues.
  - Future expansions: `slo-monitor.yml`, `backup.yml` for Supabase dump, `plan-validator.yml`.

- **Orchestration Layer** (`orchestration/`):
  - `cost.py`: provides `estimate(plan)` and `check_budget(plan)` helpers referenced in workflows.
  - `plan/current_plan.json`: canonical plan used by GitHub Actions to decide automation steps; includes degrade branch for budget exhaustion.
  - Manus briefs (v3.1 cost-aware) to keep Manus tasks aligned with “last-mile” constraints.

- **Data Persistence**:
  - **Google Sheets**: Columns `[line_user_hash, display_name, status, tags, registered_at, last_active_at, source_article]`. Updates executed via Manus Gmail/Calendar connectors or dedicated script using service account.
  - **Supabase (optional)**: Table `progress_events` capturing webhook telemetry; fallback is GitHub run logs if Supabase unavailable.

- **Docs & Tooling**:
  - `.cursorrules` ensures Cursor development guardrails.
  - `docs/RUNBOOK.md` describing stop/recover/rollback, monitoring, budget rules.
  - `tests/` folder to contain unit/integration tests (signature verification, idempotency, cost estimator, failure injection).

### Technology Choices
- **Edge runtime**: Supabase Edge Functions (Deno) is default per earlier guidance—supports crypto APIs and easy deployment; Cloudflare Workers is alternative.
- **Languages**: TypeScript for Edge (strict typing, better linting), Python 3.11 for orchestration/testing utilities.
- **Persistence**: Google Sheets chosen as interim CRM for low overhead; hashed identifiers satisfy compliance.
- **Messaging**: LINE Messaging API with guardrail helper; Manus limited to Gmail/Calendar operations when essential.

### Alternatives Considered
| Approach | Pros | Cons | Decision |
| --- | --- | --- | --- |
| Direct backend (e.g., Supabase Edge handling full automation) | Simplifies architecture, fewer moving parts | Harder to enforce GitOps workflow, loses Actions auditing | Rejected; GitHub Actions central to governance |
| Using Manus for all messaging automation | Rapid integration with connectors | Consumes points, less control, risk of runaway costs | Rejected; keep Manus “last-mile” only |
| Storing contacts in Supabase instead of Sheets | Stronger querying, scaling | Requires DB and migrations now, higher maintenance | Deferred; Sheets acceptable for initial stage with hashed IDs |
| Pull-based telemetry (Actions polling Manus) | Simpler to implement initially | Higher latency, more API calls, misses real-time need | Rejected; push notifications recommended (ProgressEvent v1.1) |

---

## Data Models & Interfaces

### Repository Dispatch Payload (Front Door → GitHub)
```json
{
  "event_type": "line_event | manus_progress",
  "client_payload": {
    "source": "line" | "manus",
    "event_id": "uuid+timestamp hash",
    "received_at": "2024-07-01T12:34:56Z",
    "event": { /* sanitized event body */ },
    "signature_valid": true,
    "idempotency_key": "hash(event)"
  }
}
```

### LINE Event Sanitized Structure
```json
{
  "destination": "Uxxxx",
  "events": [
    {
      "type": "follow | message | postback",
      "timestamp": 1710000000000,
      "source": {
        "type": "user",
        "userId": "hash:sha256(...)"  // hashed in Front Door
      },
      "message": {
        "type": "text",
        "id": "123456",
        "text": "#参加"
      },
      "replyToken": "abcdef",
      "metadata": {
        "campaign": "note-2024-07",
        "articleId": "note-slug"
      }
    }
  ]
}
```

### ProgressEvent v1.1 (GitHub → Monitoring)
```json
{
  "event_type": "step_succeeded|step_failed|heartbeat",
  "task_id": "line-event-handler",
  "step_id": "dispatch_line_reply",
  "ts": "2024-07-01T12:35:00Z",
  "idempotency_key": "line-event-<eventId>",
  "plan_title": "LINE Event Processing",
  "metrics": {
    "latency_ms": 3456,
    "retries": 0
  },
  "context": {
    "trigger": "follow",
    "user_ref": "hash:...",
    "risk_level": "low"
  }
}
```

### Google Sheets Columns
- `line_user_hash` (string, SHA-256 of user ID + salt).
- `display_name` (string, sanitized).
- `status` (`subscribed`, `unsubscribed`, `pending`).
- `tags` (comma-separated campaign labels).
- `source_article` (note slug).
- `registered_at` (ISO timestamp).
- `last_active_at` (ISO timestamp).
- `channel` (e.g., `line`, `manus`).

---

## Testing Strategy
- **Unit Tests**:
  - Edge signature verification (valid + invalid HMAC, missing header).
  - Idempotency cache behavior (duplicate events suppressed).
  - `cost.py` estimator for various plan permutations including degrade path.
  - Guardrail footer helper ensures disclaimer appended.
  - Budget check (daily/weekly thresholds crossing) returns degrade flag.
- **Integration Tests**:
  - Simulated LINE follow event through Front Door to GitHub Actions using local Miniflare + `act` CLI.
  - Manus Progress event through pipeline verifying log update and ProgressEvent dispatch.
  - Google Sheets write using mock service account or stub Manus connector.
  - Failure injection cases (403, 429, timeout) ensuring retries/backoff paths.
- **End-to-End / Acceptance**:
  - Run scripted scenario: note CTA → LINE follow (#参加) → success reply → Sheets entry → progress telemetry recorded.
  - Budget exceed scenario to confirm degrade to LINE+ICS path and Manus call skipped.
  - Manual rollback exercise following `docs/RUNBOOK.md`.

Test automation will live under `tests/` with Python/TypeScript suites, executed via GitHub Actions (lint → unit → integration). Local developer workflow uses Cursor tasks plus `npm test`/`pytest`.

---

## Deployment & Migration Considerations
1. **Preparation**:
   - Import Cursor handover package files or recreate per spec.
   - Configure GitHub repository secrets/variables: `GH_PAT`, `LLM_ENDPOINT`, `LLM_API_KEY`, Manus & LINE credentials, progress webhook URL, Google Sheets service config.
   - Ensure `.cursorrules` committed to enforce development guardrails.
2. **Front Door Deployment**:
   - Deploy `functions/relay/index.ts` to Supabase Edge (or Cloudflare Workers) with env vars.
   - Set up KV storage for idempotency (Supabase Deno KV / Workers KV).
   - Point LINE webhook URL and Manus progress webhook to deployed endpoint.
3. **GitHub Actions**:
   - Enable required workflows (`line-event.yml`, `manus-progress.yml`) and set concurrency groups.
   - Add branch protection requiring lint/test jobs to pass.
4. **Data Migration**:
   - Backfill existing subscribers into Google Sheets (manual import, hashed before upload).
   - Optionally seed Supabase logging tables.
5. **Monitoring & Alerts**:
   - Register ProgressEvent webhook in GitHub repo settings (or use dedicated workflow to forward to monitoring service).
   - Configure UptimeRobot or equivalent to watch Front Door endpoint.
6. **Rollback Plan**:
   - Disable workflows via branch protection toggle.
   - Set `FEATURE_BOT_ENABLED=false`.
   - Revert to previous webhook endpoint if necessary.

---

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Google Sheets API quota or auth failure | Contacts not logged, compliance gap | Implement retry/backoff, queue writes via Manus fallback, alert on failure; plan migration to Supabase DB. |
| Manus budget constraints | External actions fail silently | `cost.py` budget check plus degrade path to LINE+ICS; log budget status via ProgressEvent for visibility. |
| LINE signature verification bugs | Security incident or webhook hijack | Unit tests covering signature cases; use server-provided channel secret via env; monitor 4xx rates at Front Door. |
| Idempotency lapses (duplicate processing) | Double messaging/charges | Hash event payload + timestamp; maintain short-lived cache; integration tests for duplicates. |
| Secrets misconfiguration | Production outage | Provide `requirements.md` + design doc checklists; run `gh workflow run secret-audit` script; add PR template checks. |
| Observability gaps | Slow incident response | Enforce push telemetry, ensure Supabase logging or GitHub artifact fallback, integrate with Ops alerts. |
| Compliance drift (missing guardrail) | Regulatory/brand risk | Centralized helper to append disclaimer; lint rule/test verifying `tests/test_guardrail_footer.py`. |

---

## Next Steps Toward `/sdd-tasks`
1. Validate KPI targets, messaging cadence, and Google Sheets retention policy with stakeholders.
2. Import or recreate handover package files in repo; set up baseline workflows.
3. Scaffold tests (signature, cost estimator, failure injection) and ensure GitHub Actions pipelines run locally with `act`.
4. Document secret provisioning and environment setup (README/RUNBOOK updates).
5. Schedule dry-run with sample LINE events to verify end-to-end flow.
