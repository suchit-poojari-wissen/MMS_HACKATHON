# Controller UI PR

## Summary
- Purpose: Lightweight web UI for uploads, job monitoring, artifact viewing, and final report review.

## Views
- Upload: file chooser + initial query field.
- Job List: filterable.
- Job Detail: stage timeline + logs.
- Artifact Viewer: JSON pretty-print + download.
- Final Report: render `assistant_response.json`.
 - Chatbot Console: conversational UI for Phase 6/7/8 — user enters queries, sees retrieved context, GNN predictions, and assistant responses with citations.
 - Chatbot Console: conversational UI for intake + diagnostics — shop-floor operator reports breakdowns, system performs initial triage, collects incident details (equipment, symptoms, timestamps), then progresses through Phase 6/7/8 (retrieval, GNN predictions, assistant responses with citations).
 - Incident Timeline: per-incident audit trail of actions (updates, handovers, advisor comments), with role badges and citations.
 - Shift Handover: guided view to review `handover_summary.json`, confirm checklist, assign next actions, and transition state to `awaiting-shift-handover` or `in-progress`.
 - Advisor Panel: invite advisors via secure link, control visibility, and track advisor responses.

## Requirements
- Responsive, simple layout.
- Use Controller API only; no direct backend service calls.
- Minimal auth for initial rollout (trusted network).
 - Real-time interaction: websocket or long-poll updates for streaming assistant responses.
 - Incident intake: guided form + conversational prompts to capture complete incident report before analysis begins.
 - State persistence: associate all chat messages and actions to `incident_id`; append-only transcript and event log shown in Incident Timeline.
 - RBAC-aware UI: component visibility (handover, advisor tools) depends on user role.

## Implementation Notes
- Stack: React or static HTML + Alpine.js.
- JSON viewer with code syntax highlighting.

## APIs used
- `POST /upload`, `GET /status/{job_id}`, `GET /artifact/{job_id}/{artifact_name}`.
- `GET /result/{job_id}` (phase-specific) and final report fetch.
 - Chatbot flow:
	- `POST /query` (Phase 6) → initial triage + show retrieved context and explainability.
	 - `POST /predict` (Phase 7) → show ranked root causes/MTTR.
	 - `POST /diagnose` (Phase 8) → show grounded response with citations.
	 - `POST /clarify_answer` to send user follow-ups; `POST /final_report` to save session output.
	- Intake endpoints: `POST /intake_start`, `POST /intake_update` (equipment, symptoms, images), producing a consolidated incident payload used by `/query`.
 	- Incident endpoints: `POST /incident_create`, `POST /incident_update`, `POST /incident_handover`, `POST /incident_add_advisor`, `GET /incident_get/{incident_id}`.

## Testing
- UI smoke tests for each view.
- API integration tests with mocked Controller responses.
 - Chat UX tests: multi-turn interactions; streaming display; citation links.

## Open Questions
- Exact auth mechanism (basic auth vs SSO behind reverse proxy)?
- Pagination limits for job list?
- Artifact size limits and streaming behavior?
 - Streaming protocol preference (server-sent events vs websockets)?
 - Session storage for chat transcripts (persisted under artifacts or separate store)?
 - Handover validation: required fields and checklists per equipment class?
 - Advisor onboarding: external identity or email-based tokens with audit constraints?
