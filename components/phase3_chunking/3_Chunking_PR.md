# Phase 3 — Chunking (GraniteRAG Chunker) PR

## Summary
- Purpose: Convert `docling_output.json` into text/table/figure chunks for VectorXDB ingestion and downstream KG mapping.
- Inputs: `docling_output.json`.
- Outputs: `chunks.jsonl` and `chunk_manifest.json`.

## VectorXDB Ingestion (assumptions)
- Namespace per document: `doc:{document_id}`.
- Metadata keys: `document_id`, `section_path`, `page`, `chunk_type`, `source_ref`.
- Embedding model: `text-embedding-3-large` (or equivalent), 3072 dims.
- Upsert batch size: 500 vectors; retry with exponential backoff.
- Dedup: content hash per chunk to prevent duplicate upserts.

## API
```
POST /process                # accepts docling_output.json
GET  /result/{document_id}   # returns link to chunks.jsonl
GET  /health
```

## Functional Requirements
- One paragraph/table/figure per chunk; split long paragraphs using sliding windows (300–600 tokens, 10–20% overlap).
- Include NL verbalization for tables.
- Attach `section_path` and entity tags for KG mapping.
 
## Assumptions (Chunking Params)
- `window_size_tokens`: default `400`.
- `window_overlap_pct`: default `15`.
- `max_chunk_text_len`: default `4000` chars; truncate with ellipsis.
- `nl_verbalization`: template-based with heuristics for headers/rows.

## Non-functional
- Stable chunk IDs; deterministic chunking.
- Token estimation per chunk.

## Chunk Schema (examples)
- Paragraph: `chunk_id`, `document_id`, `chunk_type`, `text`, `section_path`, `page`, `metadata {bbox, entities}`.
- Table: `chunk_id`, `chunk_type`, `table {headers, rows}`, `nl_verbalization`, `metadata {page, section_path}`.
- Image: `chunk_id`, `chunk_type`, `image_ref`, `caption`, `ocr_text`, `metadata`.

## Path Hierarchy Metadata
- Include `source_path` (root-relative file path from Controller) in each chunk's metadata.
- Use `source_path` to enable scoped chunk selection and downstream vector filtering.

## Error Handling
- Fallback chunk when table reconstruction failed: `table_reconstruction_failed=true`.

## Observability
- `/health`; metrics: chunks per document, avg tokens per chunk, windowing overlap warnings.

## Testing Strategy
- Unit: windowing logic, `nl_verbalization`, section_path propagation.
- Integration: `/process` end-to-end with Docling input; manifest correctness.
- Determinism tests across repeated runs.

## Open Questions
- Exact token window size and overlap percentage to standardize?
- Entity tagging source: heuristic vs NER model?
