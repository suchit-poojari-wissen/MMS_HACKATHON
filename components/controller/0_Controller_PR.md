# Controller Component PR

## Summary
- Purpose: Coordinate the MMS pipeline end-to-end, manage job lifecycle, store artifacts, and present status to UI.
- Scope: Orchestration of stages, lifecycle transitions, artifact persistence, and UI status exposure.
 - Job vs Incident: Jobs orchestrate document-processing stages and produce artifacts; Incidents represent real-world breakdown threads that span shifts, aggregate human inputs/evidence, and drive diagnostics. Incidents consume job outputs via citations and maintain an append-only audit trail.

## Architecture & Interfaces
- Interface: REST API.

```
POST /upload           # returns job_id
GET  /status/{job_id}
POST /run_stage        # body: { job_id, stage_name, options }
GET  /artifact/{job_id}/{artifact_name}
 
 # Incident management
 POST /incident_create        # body: { title, description, severity, source_path_prefix?, participants[] } -> incident_id
 POST /incident_update        # body: { incident_id, patch }  # append-only event; no destructive updates
 POST /incident_handover      # body: { incident_id, handover_notes, checklist[], next_actions[], attachments[] }
 POST /incident_add_advisor   # body: { incident_id, advisor_user_id | external_email, permissions }
 GET  /incident_get/{incident_id}
```

- Job lifecycle: `queued -> running -> success | failed`.
- Per-stage: status + logs retained; artifacts stored with content hashes in blob storage.

## Functional Requirements
- Retries, skip-to-stage, force-reprocess.
- Per-stage timeouts and resource constraints.
- Persist metadata in Azure SQL/COSMOS (prod) and SQLite (dev).

## Data Models (high-level)
- Job: `job_id`, state, created_at, stages[], current_stage, options.
- Stage: name, status, started_at/ended_at, logs_ref, metrics.
- Artifact: `job_id`, `artifact_name`, blob_uri, content_hash, created_at, `source_path` (root-relative file path).
 - Incident: `incident_id`, `state` (`open|in-progress|awaiting-shift-handover|resolved|archived|reopened`), `severity`, `title`, `description`, `source_path_prefix`, `participants` [{ userId, role }], `advisors` [{ userId|externalEmail, role }], `created_at`, `updated_at`.
 - IncidentEvent (audit): `event_id`, `incident_id`, `actor` { userId, role }, `timestamp`, `action` (`create|update|handover|add_advisor|chat_message|attach_artifact|state_transition`), `payload_ref` (blob_uri or hash), `citations`[], `notes`.
 - Transcript: `incident_id`, `messages` [{ message_id, author { userId, role }, time, content, citations[], state_snapshot_ref }].

## Observability
- Job metrics, per-stage latencies, failure reasons; expose counters and histograms for UI/alerts.
 - Per-incident metrics: time-to-first-response, time-in-state, handover completeness score, advisor response time.
 - Audit integrity checks: append-only sequence, hash chain optional.
 
## Cross-Cutting Behavior
- Data flow consistency: propagate `source_path` and `language` metadata end-to-end; enforce filters in retrieval.
- Durability & audit: append-only `IncidentEvent` and transcripts; idempotent upserts for KG/embeddings; blob artifacts hashed.
- Observability: health endpoints, metrics (jobs and per-incident KPIs), explainability attached to retrieval/GNN/LLM outputs.
- Security: internal trusted network, optional SSO, secrets in Key Vault, strict RBAC on endpoints.

## Deployment & Operations
- Storage: blob for artifacts; SQL/Cosmos for metadata.
- Environments: dev (SQLite) vs prod (Azure SQL/Cosmos).
 - Durability: Incident, events, transcripts stored in SQL/Cosmos; large payloads and attachments in blob. All updates are append-only; corrections logged as new events.

## File Path Hierarchy Handling
- Persist original folder hierarchy for uploaded manuals: `source_path` (e.g., `FactoryA/Line3/AHU/Manuals/ahu23.pdf`).
- Propagate `source_path` into downstream artifacts and metadata to enable scoped searches (documents/vectors).

## Testing Strategy
- Unit: lifecycle transitions, retries/timeout logic.
- Integration: REST endpoints, artifact persistence, DB writes.
- Contract: API schemas; idempotency on `run_stage`.

## Security (AuthN/Z)
- AuthN: Enterprise SSO (Azure AD/OIDC), single-tenant; service principals/managed identities for batch ingestion.
- AuthZ: RBAC roles — `admin`, `operator`, `ingestor`, `viewer`, `auditor`; scope by project.
- Secrets: store in Key Vault; all API calls require bearer JWT; optionally scoped API keys for automation.
 - Remote advisors: invite via time-bounded signed links and restricted RBAC; advisors can view timeline, propose actions, and add citations per permissions.
 
### RBAC Roles (detail)
 - `admin`: full control over configuration and incidents; cannot delete audit entries (append-only).
 - `operator`: creates incidents, reports observations, uploads supporting files, interacts with assistant; no system-level changes.
 - `supervisor`: reviews/approves handovers, transitions incident states, manages participants/advisors.
 - `engineer`: runs targeted retrieval/GNN flows, proposes fixes, records outcomes; technical focus.
 - `advisor`: external, constrained visibility; can propose actions and attach citations; limited write scope.
 - `auditor`: read-only access to audit/timeline and reports; export-only.

## Rate Limits
- Token bucket per endpoint; 429 with `Retry-After`.
- Initial ingestion (~80k docs): Upload 5 rps (burst 20); Run stage 5 rps (burst 10); Reads 20 rps (burst 50).
- Steady state: Upload 1 rps (burst 5); Run stage 2 rps (burst 5); Reads 10 rps (burst 20).

## Concurrency Policy (single-tenant)
- System: initial max 50 jobs; steady max 10 jobs.
- Per-stage caps (tunable): OCR 10; Docling 20; Chunking 50; KG 10; Embeddings 20; Retrieval 10; GNN 5; LLM Assistant 5.
- Backpressure: queue depth limits, exponential backoff, defer non-critical stages.
