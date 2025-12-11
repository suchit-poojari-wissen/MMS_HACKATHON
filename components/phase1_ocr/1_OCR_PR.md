# Phase 1 — OCR & Layout (Docling Heron) PR

## Summary
- Purpose: Use Docling Heron for OCR + layout extraction; emit `heron_output.json` compatible with Granite.
- Inputs: PDF, JPG, PNG, TIFF; optional params: `language`, `dpi_override`, `fast_mode`.
- Outputs: `heron_output.json` with `pages[]`, `blocks[] (text_line|table_candidate|image)`, bboxes, OCR confidence.

## API
```
POST /v1/process
GET  /v1/status/{job_id}
GET  /v1/result/{job_id}
GET  /health
```

## Functional Requirements
- High OCR accuracy; deterministic output; produce Heron layout blocks.
- Extract table candidates + bounding boxes; emit image refs if persisted to blob.
- Sync for small files; async job interface for large files.

## Assumptions (Heron Params)
- `language`: default `ja` (Japanese); accepts ISO 639-1 codes (supports `en` and `ja`).
- `dpi_override`: default `300`; range `200–600`.
- `fast_mode`: default `false`; when `true`, skips denoise/deskew.
- `max_pages_sync`: default `10` pages processed synchronously; above this uses async job.

## Non-functional
- Avg page time: < 3s (VM dependent).
- Deterministic outputs for identical input + config; Granite compatibility.

## Data Schema (example)
- Job result: `heron_output.json` fields: `document_id`, `pages[] {blocks[]: text_line|table_candidate|image}`, `metadata {language,dpi,confidence}`.

## Error Handling
- `UNSUPPORTED_FORMAT`, `OCR_ENGINE_ERROR`, `LOW_OCR_CONFIDENCE` (page-level warnings).

## Observability
- `/health`; expose page processing latency, OCR confidence distribution, error counts.

## Deployment & Operations
- CPU optimizations (OpenVINO) on Intel; fallback/run cloud OCR (Azure Form Recognizer) for low-confidence critical tables.
- Resource limits: per-job CPU cap 2 vCPU; memory 4 GiB.
- Throughput target: >= 0.3 pages/sec per vCPU.
 - Multilingual OCR: enable language auto-detect for mixed English/Japanese pages; per-page language recorded in metadata.

## Testing Strategy
- Unit: format detection, pre-processing, block extraction.
- Integration: `/process` multipart + blob input; image persistence.
- Determinism tests: same input/config yields identical `ocr_output.json`.

## Open Questions
- Confidence threshold to trigger cloud OCR fallback?
- Max file sizes and ZIP depth limits?
- Sync cutoff: e.g., pages <= N treated synchronously?
