
# Phase 3 – Chunking (GraniteRAG Chunker)

## Purpose
Convert docling_output.json into text, table, and figure chunks for VectorXDB ingestion.

## Inputs
- docling_output.json

## Outputs
- chunks.jsonl
- chunk_manifest.json

## Chunk Rules
- One paragraph per chunk
- One table per chunk with NL verbalization
- One figure per chunk
- Split long paragraphs with sliding windows

## Example Chunk
```json
{
  "chunk_id": "DOC_0001_p_1",
  "chunk_type": "paragraph",
  "text": "Error code E47 indicates high discharge...",
  "section_path": ["Compressor Fault Codes"],
  "page": 3
}
```

## Requirements
- Stable chunk IDs
- Deterministic chunking
- Token estimation
