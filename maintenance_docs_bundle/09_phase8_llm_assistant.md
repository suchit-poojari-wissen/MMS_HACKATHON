# Phase 8 — LLM Diagnostic Assistant

## Purpose
Generate final human-facing diagnostic guidance grounded in retrieved evidence and GNN predictions.

## Inputs
- `retrieved_context.json`
- `gnn_predictions.json` (optional)
- Reporter inputs (observations, sensor readings)

## Outputs
- `assistant_response.json` containing:
  - diagnosis, ranked_causes, estimated_mttr_minutes
  - diagnostic_steps[] with step_no, description, safety_warnings
  - spares[]
  - evidence_references[] (chunk ids)
  - clarifying_questions[]

## Example output
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

## Functional Requirements
- Prompt engineering templates with grounding and citation enforcement
- JSON schema validation on LLM output
- Mechanism to request clarifying questions and accept answers

## Non-functional Requirements
- Median response latency < 3s (cloud LLM dependent)
- Redaction and logging practices to avoid leaking sensitive info

## API
```
POST /diagnose
POST /clarify_answer
POST /final_report
GET /health
```

## Error handling
- INVALID_LLM_OUTPUT -> attempt auto-repair + retry (limit 2)
- PROVIDER_UNAVAILABLE -> fallback to cached templates or degraded mode
