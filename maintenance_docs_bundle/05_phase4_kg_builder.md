# Phase 4 — Knowledge Graph Builder (Neo4j)

## Purpose
Create and maintain a domain-specific maintenance knowledge graph. Nodes represent Equipment, Component, ErrorCode, Procedure, SparePart, DocumentSection. Edges represent HAS_COMPONENT, HAS_ERROR_CODE, RECOMMENDS_ACTION, REQUIRES_SPARE, MENTIONED_IN_CHUNK.

## Inputs
- `chunks.jsonl` (from Phase 3)
- Optional: `docling_output.json` for additional context

## Outputs
- `graph_nodes.jsonl`
- `graph_edges.jsonl`
- `chunk_graph_links.jsonl`

## Node schema (example)
```json
{
  "node_id":"Error:E47",
  "labels":["ErrorCode"],
  "properties":{"code":"E47","description":"High discharge temperature","sources":["DOC_1234"]}
}
```

## Edge schema (example)
```json
{
  "edge_id":"e_1",
  "source":"Component:Compressor",
  "target":"Error:E47",
  "type":"HAS_ERROR_CODE",
  "properties":{"confidence":0.93,"source_chunk":"DOC_1234_p_1"}
}
```

## Functional Requirements
- Hybrid entity extraction using deterministic rules + LLM-assisted confirmation for ambiguous entities.
- Idempotent upsert behavior using MERGE semantics in Neo4j.
- Provenance metadata: source_chunk_id, confidence, extract_method.

## Non-functional Requirements
- Support incremental ingestion; ability to re-ingest documents without duplication.
- Neo4j sizing: for 100k nodes, recommend 64–128GB RAM in prod.

## API
```
POST /ingest_chunks   # accepts chunks.jsonl or pointer
POST /upsert_nodes
POST /upsert_edges
GET /graph_export/{document_id}
GET /health
```

## Error handling
- DUPLICATE_ENTITY_CONFLICT (use canonicalization rules)
- NEO4J_WRITE_ERROR
