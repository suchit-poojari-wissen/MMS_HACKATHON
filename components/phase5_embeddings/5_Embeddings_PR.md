# Phase 5 — Embeddings & VectorXDB PR

## Summary
- Purpose: Generate embeddings for chunks and store in VectorXDB.
- Inputs: `chunks.jsonl` (text and table NL verbalization).
- Outputs: Vector collection: `{ id, vector, metadata }`.

## API
```
POST /ingest_batch
POST /search
GET  /collection_stats
GET  /health
```

## Functional Requirements
- Batch embedding via cloud (Azure OpenAI embeddings recommended).
- Metadata-filtered search; upsert semantics for re-ingestion.

## Non-functional
- Scale to ~800k vectors; index sizing accordingly.
- Search latency: median < 200 ms for top-10.

## Record Schema (example)
- `{ id, vector[], metadata { chunk_type, document_id, entities[], source_path } }`.

## Error Handling
- `EMBEDDING_API_RATE_LIMIT` → retry backoff.
- `VECTOR_DB_OUT_OF_MEMORY` → downsize index or scale cluster.

## Observability
- `/health`; metrics: batch throughput, embedding API latency, index build time.

## Testing Strategy
- Unit: metadata filter application, upsert idempotency.
- Integration: `/ingest_batch` end-to-end with `chunks.jsonl`; `/search` semantics.
- Performance: search latency and index build under ~800k vectors.

## Assumptions
- Embedding model: `text-embedding-3-large`, dims 3072; batch size 256; rate-limit aware with token bucket.
 - Vector DB: VectorXDB; distance `Cosine`; payload/index on `document_id`, `chunk_type`, `entities`, `source_path`, `language`.
- Namespace: single collection `mms_chunks`; `id` equals `chunk_id`; dedup via content hash.
 - Multilingual embeddings: use same model for English/Japanese; store `language` in metadata to enable language-aware retrieval.
