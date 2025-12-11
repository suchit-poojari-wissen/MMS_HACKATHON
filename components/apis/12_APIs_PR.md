# Consolidated API PR (Phase 1–8 + Controller)

## Auth
- Internal trusted network; no auth headers for inter-service calls.
- Controller UI protected by network restrictions; future SSO optional.

## Controller
- `POST /upload` → `{ job_id }`
- `GET /status/{job_id}`
- `POST /run_stage` `{ job_id, stage_name, options }`
- `GET /artifact/{job_id}/{artifact_name}`
 - `POST /incident_create` → `{ incident_id }`
 - `POST /incident_update` (append-only)
 - `POST /incident_handover`
 - `POST /incident_add_advisor`
 - `GET /incident_get/{incident_id}`

## Phase 1 — OCR
- `POST /process` (multipart or JSON pointer) → `{ job_id, status_url }`
- `GET /status/{job_id}`
- `GET /result/{job_id}` → `ocr_output.json`

## Phase 2 — Docling
- `POST /process` `{ ocr_result_url }` → `{ status_url, result_url }`
- `GET /result/{document_id}`

## Phase 3 — Chunker
- `POST /process` `{ docling_url }` → chunks URL
- `GET /result/{document_id}`

## Phase 4 — KG Builder
- `POST /ingest_chunks` (body: `chunks.jsonl` or pointer)
- `POST /upsert_nodes` (body: `graph_nodes.jsonl`)
- `POST /upsert_edges` (body: `graph_edges.jsonl`)
- `GET /graph_export/{document_id}`

## Phase 5 — Embeddings
- `POST /ingest_batch` (chunks list)
- `POST /search` `{ query, top_k, filters }`
- `GET /collection_stats`

## Phase 6 — Retrieval
- `POST /query` `{ query, user_context, top_k }` → `retrieved_context.json`

## Phase 7 — GNN
- `POST /predict` (subgraph + features) → `gnn_predictions.json`
- `POST /train` (async)

## Phase 8 — LLM Assistant
- `POST /diagnose` (retrieved_context + optional gnn_predictions) → `assistant_response.json`
- `POST /clarify_answer`
- `POST /final_report`
 - Intake (controller-coordinated): `POST /intake_start`, `POST /intake_update` → `incident_brief.json`

## Error Model (standardized)
- 400 `BAD_REQUEST`
- 404 `NOT_FOUND`
- 422 `UNSUPPORTED_FORMAT`
- 500 `INTERNAL_ERROR`
- 503 `DEPENDENCY_UNAVAILABLE`

## Notes
- All result endpoints return either JSON payload or a signed URL to blob.
- Consistent pagination/filtering for list endpoints where applicable.
- Prefer idempotent POSTs for upsert endpoints.
