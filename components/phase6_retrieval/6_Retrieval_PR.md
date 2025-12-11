# Phase 6 — Hybrid Retrieval Engine (Graph + Vector) PR

## Summary
- Purpose: For a user query + optional equipment context, return merged context combining vector hits and KG evidence.
- Inputs: `{ query, user_context, top_k }`.
- Outputs: `retrieved_context.json` with `resolved_entities`, `vector_hits`, `subgraph`, `explainability`.

## API
```
POST /query
GET  /status/{query_id}
GET  /health
```

## Functional Requirements
- Query embedding via embed service.
- Vector search (`top_k`) over chunk collection.
- Entity resolution using KG canonical IDs or alias index.
- Subgraph expansion (1–3 hops) with filters; limit breadth.
- Merge and rank results via configurable weighting (vector score + graph evidence).
 - Scoped search: support filters by `source_path` prefix to narrow documents/vectors based on folder hierarchy.
 - Language-aware retrieval: allow filter by `language` and perform bilingual query expansion when mixed-language evidence exists.

## Non-functional
- End-to-end latency < 400 ms.
- Attach explainability per chunk: features used (e.g., vector_sim, entity_mentions, edge types).

## Output Example
```json
{
  "query_id":"q_123",
  "query":"AHU showing E47 after restart",
  "resolved_entities":["Error:E47","Equipment:AHU-23"],
  "vector_hits":[{"chunk_id":"DOC_1234_tbl_1","score":0.92}],
  "subgraph":{"nodes":[{"id":"Error:E47","type":"ErrorCode"}],"edges":[]},
  "explainability":[{"chunk_id":"DOC_1234_tbl_1","reason":"vector_sim(0.92) & mentions(Error:E47)"}]
}
```

## Error Handling
- `ENTITY_NOT_FOUND` → fallback to vector-only search.
- `SUBGRAPH_TOO_LARGE` → cap expansion depth; return warning.

## Observability
- `/health`; metrics: latency, top_k distribution, graph expansion depth, explainability attachment rate.

## Testing Strategy
- Unit: entity resolution, weighting function.
- Integration: `/query` end-to-end; KG + vector fusion.
- Performance: latency under load; subgraph expansion caps.

## Assumptions
- Weighting: `final_score = 0.7*vector_sim + 0.3*graph_signal`.
- Graph expansion: default depth 2; max nodes 500 per query.
- Embed model reused from Phase 5; cache recent query embeddings for 5 minutes.
 - Filters: `source_path_prefix` accepted in query to constrain both vector and KG contexts.
 - Multilingual: if query language differs from chunk language, perform cross-lingual retrieval using embeddings; rank boosted for same-language matches.
