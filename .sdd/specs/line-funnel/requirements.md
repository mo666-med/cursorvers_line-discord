# Cursorvers LINE Funnel – Requirements

## Business Objectives
- Convert note article readers into LINE subscribers at ~40% opt-in, then nurture them toward consulting engagements (events, advisory retainers).
- Maintain medical safety guardrails: no individual diagnoses, always append standardized disclaimer, encourage emergency care when needed.
- Keep operations lightweight and maintainable through GitHub Actions + Edge deployment with Manus limited to “last-mile” integrations for point efficiency.

## Functional Requirements
1. Accept webhooks from LINE and Manus via Front Door (Edge/Workers) with signature verification and idempotency handling.
2. Dispatch validated events into GitHub via `repository_dispatch`, triggering workflows for planning, analysis, and messaging.
3. Automate outbound LINE messaging for:
   - New note article announcements.
   - Distribution of supplementary materials (e.g., guides) upon request.
   - Promotional notifications for events, webinars, or advisory services.
   Messages must include safety guardrail footer.
4. Store LINE subscriber metadata (hashed identifiers, subscription timestamps, tags) in Google Sheets for interim CRM and auditing.
5. Provide cost estimation and degradation: call Manus cost estimator before external actions; degrade to LINE + ICS fallback if daily/weekly budget thresholds breached.
6. Offer real-time progress telemetry via push notifications (ProgressEvent v1.1) into GitHub/monitoring.

## Non-Functional Requirements
- Security: Secrets via GitHub/OIDC only; sanitize payloads to minimize PHI; ensure verified domain usage in URLs.
- Reliability: Actions must enforce concurrency controls, retries, and idempotency for repeat events.
- Observability: Track webhook success rates, Manus invocation counts, heartbeat signals, and budget usage; log to Supabase or interim storage.
- Maintainability: Keep code modular (Edge TS, Actions YAML, Python orchestration), include unit tests (signature verification, failure injection) and documentation (Runbook).
- Compliance: Ensure guardrail messaging, hashed identifiers before persistence, audit-ready logs.

## Assumptions & Dependencies
- Google Sheets access via Manus or service account is available with necessary quota.
- Supabase (or equivalent) available for logging; fallback is GitHub artifacts/logs if deferred.
- Verified domain DNS + Edge deployment pipeline exist but details pending.
- Stakeholder KPIs beyond 40% opt-in will be aligned during implementation; design keeps metrics extensible.

## Open Questions
- Final cadence/segmentation for LINE messaging (frequency limits, targeting).
- Retention policy and access controls for Google Sheets data.
- Confirmation of fallback channels when Manus budget forces degradation (e.g., ICS delivery path).
