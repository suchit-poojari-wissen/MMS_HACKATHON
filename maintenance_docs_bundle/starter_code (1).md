
# Starter Source Code & Best GitHub Repositories

This file includes curated, popular, **applied** repositories that actually use:
- Docling Heron (OCR + layout)
- Docling Granite (structure extraction)
- GraniteRAG (chunking + retrieval)
- KG extraction (DeepRAG / GraphRAG)
- GNN reasoning examples
- Orchestration systems

---

# ✅ 1. Core Ingestion Pipeline Repositories (Heron + Granite)

## ⭐ GraniteRAG  
https://github.com/ibm-granite/granite-rag

## ⭐ Granite Snack Cookbook  
https://github.com/ibm-granite/granite-snack-cookbook

## ⭐ Docling Examples  
https://github.com/ibm-granite/docling  
https://github.com/ibm-granite/docling-heron

---

# ✅ 2. Knowledge Graph & Hybrid Retrieval

## ⭐ DeepRAG  
https://github.com/infiniflow/deepRAG

## ⭐ AGIHouse GraphRAG  
https://github.com/AGIHouse/graph-rag

---

# ✅ 3. Vector DB Integration (using ChromaDB now; swap to VectorXDB later)

## ⭐ Jina AI Awesome RAG  
https://github.com/jina-ai/awesome-rag

## ⭐ Qdrant Examples  
https://github.com/qdrant/examples

## ⭐ ChromaDB (Phase 5 starter)
Repo: https://github.com/chroma-core/chroma
Examples: https://github.com/chroma-core/chroma/tree/main/examples
Notes:
- Simple local setup, Python SDK, persistence
- Supports metadata fields we need (e.g., `language`, `source_path`)
- We will mirror APIs/filters to ease a later swap to VectorXDB

---

# ✅ 4. GNN Fault Diagnosis

## ⭐ Industrial GNN Fault Diagnosis  
https://github.com/larocs/gnn-fault-diagnosis

## ⭐ PyTorch Geometric Examples  
https://github.com/pyg-team/pytorch_geometric/tree/master/examples

---

# Starter Code (Pipeline Skeleton)

```python
# Phase 1 — Heron OCR
from docling_heron import HeronOCR
ocr = HeronOCR()
result = ocr.process("input.pdf")
open("heron_output.json","w").write(result.json())
```

```python
# Phase 2 — Granite Structure Extraction
from docling import GraniteProcessor
j = open("heron_output.json").read()
doc = GraniteProcessor().process_json(j)
open("docling_output.json","w").write(doc.json())
```
 
# Phase-to-Repo Usage Map (Applied Elements)

| Phase | Repo | What we use | Purpose |
|------|------|-------------|---------|
| 1 — Heron OCR/Layout | `docling-project/docling` | CLI/Python `DocumentConverter` with default Heron layout | Ingest PDF, run Heron for layout/OCR, emit structured JSON for Granite |
| 2 — Granite Structure | `docling-project/docling` | CLI `--pipeline vlm --vlm-model granite_docling` | Run GraniteDocling VLM to enrich structure (sections, tables, figures) |
| 2 — Granite Structure | `ibm-granite-community/granite-snack-cookbook` | Notebook `recipes/RAG/Granite_Docling_RAG.ipynb` | Reference flows combining Granite + Docling for downstream RAG |
| 3 — Chunking/RAG | `chroma-core/chroma` | `examples/` clients for ingestion/search | Demonstrate chunk ingestion with metadata (language, source_path), and basic queries |
| 3 — Chunking/RAG | `run-llama/llama_index` | loaders + node parsers + chunkers | Practical chunking strategies, windowed overlap, and citation-friendly nodes |
| 3 — Chunking/RAG | `ibm-granite-community/granite-snack-cookbook` | Granite+Docling RAG notebook | Aligns extraction outputs with downstream chunking patterns |
| 4 — Hybrid Retrieval | `microsoft/graphrag` | graph build + query pipeline | Example hybrid graph/text retrieval with explainability |
| 5 — Embeddings/Vector DB | `chroma-core/chroma` | Python client + persistence | Store embeddings + metadata filters, prepare for retrieval |
| 6 — Retrieval | `deepset-ai/haystack` | pipeline + retrievers + re-rankers | Hybrid retrieval patterns, re-ranking before LLM |
| 6 — Retrieval | `chroma-core/chroma` | `examples/` query flows | Filtered queries leveraging stored metadata |
| 7 — GNN | `pyg-team/pytorch_geometric` | `examples/` GNN models | Reference implementations for graph-based reasoning |
| 7 — GNN | `dmlc/dgl` | tutorials/examples | Alternative GNN toolkit examples |
| 8 — LLM Assistant | `microsoft/graphrag` | LLM + graph reasoning demos | Grounded assistant flows with citations and structured outputs |

Notes:
- Applied examples only; no library internals.
- Docling provides Heron by default; GraniteDocling via VLM CLI.
- ChromaDB is the vector store for Phase 5–6; swap to VectorXDB later.


```python
# Phase 3 — Chunking (GraniteRAG)
from granite_rag import ChunkBuilder
builder = ChunkBuilder()
chunks = builder.build("docling_output.json")
with open("chunks.jsonl","w") as f:
    for c in chunks:
        f.write(c.json() + "\n")
```


---

# Docker Images Cheat Sheet (for local development)

- Neo4j Community:
    - Image: `neo4j:5-community`
    - Quick start: `docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5-community`

- VectorXDB:
    - Image: `vectorxdb:latest` (placeholder)
    - Quick start: `docker run -p 8080:8080 -p 6333:6333 vectorxdb:latest`

- ChromaDB:
    - Image: `ghcr.io/chroma-core/chroma:latest`
    - Quick start: `docker run -p 8000:8000 ghcr.io/chroma-core/chroma:latest`

- Docling Heron:
    - Image: `ghcr.io/ibm-granite/docling-heron:latest`
    - Quick start: `docker run -p 8081:8081 ghcr.io/ibm-granite/docling-heron:latest`

- Docling Granite:
    - Image: `ghcr.io/ibm-granite/docling:latest`
    - Quick start: `docker run -p 8082:8082 ghcr.io/ibm-granite/docling:latest`

- GraniteRAG:
    - Image: `ghcr.io/ibm-granite/granite-rag:latest`
    - Quick start: `docker run -p 8083:8083 ghcr.io/ibm-granite/granite-rag:latest`

- Optional: NGINX reverse proxy (for UI/auth experiments)
    - Image: `nginx:stable`
    - Quick start: `docker run -p 80:80 nginx:stable`

Notes:
- Prefer docker-compose to wire services, networks, and persistent volumes.
- Use bind mounts/volumes for data (`chunks.jsonl`, KG exports, vector collections).
- Secure images with env vars and non-default credentials for production.
