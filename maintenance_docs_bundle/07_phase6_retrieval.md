# Phase 6 — Hybrid Retrieval Engine (Graph + Vector)

## Purpose
Given a user query and optional equipment context, retrieve a merged context combining vector hits and graph evidence.

## Inputs
- Query payload: {query, user_context, top_k}

## Outputs
- `retrieved_context.json` containing resolved_entities, vector_hits, subgraph, explainability

## Example output
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

## Functional Requirements
- Embed query via embed-service
- Vector search (top_k)
- Entity resolution (via KG or alias index)
- Subgraph expansion (1-3 hops with filters)
- Merge and rank results using configurable weighting

## Non-functional Requirements
- End-to-end retrieval latency target < 400 ms
- Explainability data attached to each returned chunk

## API
```
POST /query
GET /status/{query_id}
GET /health
```

## Error handling
- ENTITY_NOT_FOUND -> fallback to vector-only search
- SUBGRAPH_TOO_LARGE -> limit expansion depth and return warning
