# Phase 4 — Knowledge Graph Builder (Neo4j) PR

## Summary
- Purpose: Build and maintain the maintenance KG from chunks; nodes: Equipment, Component, ErrorCode, Procedure, SparePart, DocumentSection; edges: HAS_COMPONENT, HAS_ERROR_CODE, RECOMMENDS_ACTION, REQUIRES_SPARE, MENTIONED_IN_CHUNK.
- Inputs: `chunks.jsonl` (+ optional `docling_output.json`).
- Outputs: `graph_nodes.jsonl`, `graph_edges.jsonl`, `chunk_graph_links.jsonl`.

## API
```
POST /ingest_chunks        # accepts chunks.jsonl or pointer
POST /upsert_nodes
POST /upsert_edges
GET  /graph_export/{document_id}
GET  /health
```

## Functional Requirements
- Hybrid entity extraction: deterministic rules + LLM-assisted confirmation for ambiguous entities.
- Idempotent upserts via Neo4j MERGE semantics; canonicalization to avoid duplicates.
- Provenance on all relationships: `source_chunk_id`, `confidence`, `extract_method`.
 - Terminology normalization and alias resolution: maintain synonym dictionary (e.g., "overload trip" ≡ "OL trip"); apply before upserts.

## Non-functional
- Incremental ingestion; safe re-ingest without duplication.
- Neo4j sizing guidance: ~100k nodes → 64–128GB RAM (prod).

## Schemas (examples)
- Node: `node_id`, `labels[]`, `properties { code|name|description|sources[] }`.
- Edge: `edge_id`, `source`, `target`, `type`, `properties { confidence, source_chunk }`.

## Error Handling
- `DUPLICATE_ENTITY_CONFLICT` (resolved by canonicalization rules).
- `NEO4J_WRITE_ERROR`.

## Observability
- `/health`; metrics: nodes/edges upserted, duplicate resolution counts, Neo4j write latencies.

## Testing Strategy
- Unit: canonicalization rules, MERGE idempotency, provenance mapping.
- Integration: `/ingest_chunks` → upsert nodes/edges in Neo4j; export round-trip.
- Performance: batch upsert throughput; memory usage with 100k nodes.

## Assumptions
- Canonical IDs: `Type:Name` (e.g., `Error:E47`); case-insensitive matching with normalization.
- Batch size: 1k nodes/edges per transaction; exponential backoff on transient errors.
- LLM confirmation threshold: trigger when rule-based confidence < 0.8.
 - Alias index: per-entity-type alias map persisted in KG; normalized labels stored alongside canonical IDs.
 - Data hygiene: de-duplicate near-identical nodes/edges using content hashes and similarity; minimum support threshold before a cause is promoted.
