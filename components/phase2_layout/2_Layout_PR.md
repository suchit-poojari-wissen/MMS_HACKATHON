# Phase 2 — Structure Extraction (Docling Granite) PR

## Summary
- Purpose: Convert Heron OCR output into hierarchical structure using Docling Granite; emit `docling_output.json`.
- Inputs: `heron_output.json`.
- Outputs: `docling_output.json` with sections, paragraphs, tables, images, confidence.

## API
```
POST /process            # accepts heron_output.json
GET  /result/{document_id}
GET  /health
```

## Functional Requirements
- Accurate heading detection; hierarchical section tree via font/spacing heuristics.
- Table reconstruction; normalize multi-line cells.
- Figures/caption extraction via proximity heuristics.
- Emit confidence + warnings for ambiguous structures.

## Non-functional
- Deterministic output for identical inputs.
- Table reconstruction F1 >= 0.9 on reference corpus.

## Data Schema (example)
- `docling_output.json`: `sections[] {id,title,level,start_page,end_page}`, `paragraphs[] {id,section_id,page,bbox,text,language}`, `tables[] {id,section_id,page,headers[],rows[],language}`, `images[] {id,page,caption,image_ref,language}`; document-level `language` and per-element overrides.

## Error Handling
- `DOC_PARSING_ERROR`, `TABLE_RECONSTRUCTION_FAILED` (fallback to raw_text chunk).

## Observability
- `/health`; metrics: parsing latency, table F1, ambiguous element count.

## Testing Strategy
- Unit: heading detection, paragraph grouping, caption proximity.
- Integration: `/process` with `ocr_output.json` and PDF; result schema.
- Benchmarks: table F1 on corpus; determinism checks.

## Open Questions
- Minimum confidence thresholds for table acceptance?
- Handling of nested lists and edge cases in complex layouts?
