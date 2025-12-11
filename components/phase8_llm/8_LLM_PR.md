# Phase 8 — LLM Diagnostic Assistant PR

## Summary
- Purpose: Produce human-facing diagnostic guidance grounded in retrieval evidence and optional GNN predictions.
- Inputs: `retrieved_context.json`, optional `gnn_predictions.json`, reporter inputs (observations, sensor readings).
- Outputs: `assistant_response.json` with diagnosis, ranked_causes, estimated_mttr_minutes, diagnostic_steps, spares, evidence_references, clarifying_questions.

## API
```
POST /diagnose
POST /clarify_answer
POST /final_report
GET  /health
```
### Intake APIs (controller-coordinated)
- `POST /intake_start` → begins triage session, returns `intake_id`.
- `POST /intake_update` → adds operator inputs (equipment, symptoms, images, timestamps); on completion emits `incident_brief.json` for Phase 6.
 - Per-incident state: maintain conversation state keyed by `incident_id`; include role context (`operator|supervisor|engineer|advisor`) to tailor responses and visibility.
 - Handover support: generate structured `handover_summary.json` capturing hypotheses, evidence, pending tests, and next actions; stored with the incident for shift transitions.

## Functional Requirements
- Prompt templates enforce grounding + citations; JSON schema validation on LLM output.
- Clarifying question loop: request → user answer → update diagnosis.
- Safety warnings included in diagnostic steps.
 - Intake triage: support an initial incident intake mode to collect equipment, symptoms, images, and timestamps from operators before analysis; generate a summarized incident brief used as context.

## Non-functional
- Median response latency < 3s (cloud LLM dependent).
- Redaction + logging to avoid sensitive data leakage.

## Example Output
```json
{
  "query_id":"q_123",
  "diagnosis":"Likely cause: Sensor misalignment",
  "ranked_causes":[{"cause":"Sensor misalignment","score":0.82},{"cause":"Low airflow","score":0.62}],
  "estimated_mttr_minutes":45,
  "spares":[{"id":"SP-123","name":"Temp sensor assembly","qty":1}],
  "diagnostic_steps":[{"step_no":1,"title":"Isolate power","description":"Shut down AHU..."}],
  "evidence_references":["DOC_1234_tbl_1","DOC_987_p_14"]
}
```

## Error Handling
- `INVALID_LLM_OUTPUT` → auto-repair attempts + retry (limit 2).
- `PROVIDER_UNAVAILABLE` → fallback to cached templates or degraded mode.

## Observability
- `/health`; metrics: response latency, repair retry rate, clarification loops per session.
 - Per-incident timelines: record assistant actions (prompts, outputs) into append-only transcript linked to Controller audit events.

## Testing Strategy
- Unit: prompt template rendering, JSON schema validator.
- Integration: `/diagnose` with Phase 6 context + optional GNN input.
- Resilience: fallback behavior on provider outage; output repair paths.

## Assumptions
- LLM: `gpt-4.1` or equivalent with JSON mode; temperature 0.2; max tokens 2k.
- Grounding: attach citations from `vector_hits` and KG subgraph; decline uncited claims.
- Redaction: strip PII from reporter inputs; log hashes for audit.
 - Advisor visibility: adhere to Controller-provided visibility and RBAC; advisors can suggest actions and attach citations which are logged as audit events.
