# Phase 5 — Embeddings & Vector Store

## Purpose
Generate embeddings for chunks and store in a vector database (Milvus / Qdrant / Weaviate).

## Inputs
- `chunks.jsonl` (text or nl_verbalization for tables)

## Outputs
- Vector collection with records: {id, vector, metadata}

## Example record
```json
{
  "id":"DOC_1234_p_1",
  "vector":[0.234,-0.112,...],
  "metadata":{"chunk_type":"paragraph","document_id":"DOC_1234","entities":["Error:E47"]}
}
```

## Functional Requirements
- Batch embeddings using cloud providers (Azure OpenAI embeddings recommended).
- Support filters by metadata during search
- Upsert behavior for re-ingestion.

## Non-functional Requirements
- Handle ~800k vectors; index memory sizing accordingly.
- Search latency target: median < 200 ms for top-10.

## API
```
POST /ingest_batch
POST /search
GET /collection_stats
GET /health
```

## Error handling
- EMBEDDING_API_RATE_LIMIT -> retry backoff
- VECTOR_DB_OUT_OF_MEMORY -> recommend smaller index or scaling
