
# Phase 2 – Structure Extraction (Docling Granite)

## Purpose
Convert Heron OCR output into structured hierarchical document representation using Docling Granite.

## Inputs
- heron_output.json

## Outputs
- docling_output.json:
  - sections[]
  - paragraphs[]
  - tables[]
  - figures[]
  - metadata

## Example
```json
{
  "sections": [
    {"id": "sec_1", "title": "Compressor Fault Codes", "level": 1}
  ],
  "paragraphs": [
    {"id": "p_1", "section_id": "sec_1", "text": "Error code E47 indicates..."}
  ]
}
```

## Requirements
- Accurate heading detection
- Table reconstruction
- Deterministic structure extraction
