# API Definitions (Consolidated)

This file collects OpenAPI-style endpoint definitions and request/response examples used by all phases.

## Auth model
Internal trusted network: no authentication headers required for inter-service calls. Controller UI may be protected by network restrictions.

---

## Phase 1 - OCR
POST /v1/process (multipart or JSON pointer)
Response 200: { "job_id": "...", "status_url": "/v1/status/{job_id}" }
GET /v1/status/{job_id}
GET /v1/result/{job_id} -> timestamped heron_output JSON and optional assets
GET /health -> service diagnostics

## Phase 2 - Docling
POST /process { "ocr_result_url": "..." } -> returns status / result_url
GET /result/{document_id}

## Phase 3 - Chunker
POST /process { "docling_url": "..." } -> returns chunks.jsonl url
GET /result/{document_id}

## Phase 4 - KG Builder
POST /ingest_chunks  (body: chunks.jsonl or pointer)
POST /upsert_nodes (body: graph_nodes.jsonl)
POST /upsert_edges (body: graph_edges.jsonl)
GET /graph_export/{document_id}

## Phase 5 - Embeddings
POST /ingest_batch (body: chunks list)
POST /search { "query": "...", "top_k": 10, "filters": {...} }
GET /collection_stats

## Phase 6 - Retrieval
POST /query { "query":"...", "user_context": {...}, "top_k": 10 }
Response: retrieved_context.json

## Phase 7 - GNN
POST /predict (body: subgraph + features) -> gnn_predictions.json
POST /train (async)

## Phase 8 - LLM Assistant
POST /diagnose (body: retrieved_context + gnn_predictions?) -> assistant_response.json
POST /clarify_answer
POST /final_report

## Controller
POST /upload (multipart) -> { job_id }
GET /status/{job_id}
POST /run_stage { job_id, stage_name, options }
GET /artifact/{job_id}/{artifact_name}

Errors standardized (sample codes):
- 400 BAD_REQUEST
- 404 NOT_FOUND
- 422 UNSUPPORTED_FORMAT
- 500 INTERNAL_ERROR
- 503 DEPENDENCY_UNAVAILABLE
