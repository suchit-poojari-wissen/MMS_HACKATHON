# Diagrams (Mermaid)

## End-to-end pipeline
```mermaid
flowchart TD
    A[Document Input: PDF / DOCX / PPTX / Images] --> B[Phase 1: OCR Service]
    B --> C[Phase 2: Docling Structure Extraction]
    C --> D[Phase 3: Chunker]
    D --> E[Phase 4: KG Builder]
    D --> F[Phase 5: Embeddings & Vector Store]
    E --> G[Phase 6: Hybrid Retrieval Engine]
    F --> G
    G --> H[Phase 7: GNN Reasoning (optional)]
    H --> I[Phase 8: LLM Diagnostic Assistant]
    I --> J[Final Diagnostic Report]
```

## Ingestion Sequence (detailed)
```mermaid
sequenceDiagram
    participant U as User/UI
    participant CTRL as Controller
    participant P1 as OCR
    participant P2 as Docling
    participant P3 as Chunker
    participant P4 as KG
    participant P5 as Embeddings
    U->>CTRL: Upload document
    CTRL->>P1: POST /process (file)
    P1-->>CTRL: job_id, status_url
    CTRL->>P2: POST /process (ocr_result_url)
    P2-->>CTRL: docling_output_url
    CTRL->>P3: POST /process (docling_url)
    P3-->>CTRL: chunks_url
    CTRL->>P4: POST /ingest_chunks (chunks_url)
    CTRL->>P5: POST /ingest_batch (chunks subset)
```

## Retrieval Sequence
```mermaid
sequenceDiagram
    participant User as User
    participant CTRL as Controller
    participant RET as Retrieval
    participant GNN as GNN
    participant LLM as LLM Assistant
    User->>CTRL: submit query
    CTRL->>RET: POST /query
    RET-->>CTRL: retrieved_context.json
    CTRL->>GNN: POST /predict (optional)
    GNN-->>CTRL: gnn_predictions.json
    CTRL->>LLM: POST /diagnose (retrieved + gnn)
    LLM-->>CTRL: assistant_response.json
    CTRL-->>User: final response
```

## Deployment Topology
```mermaid
flowchart LR
    subgraph Azure_VM[Azure VM (Prod)]
        subgraph Docker[Docker Network]
            CTRL[Controller]
            UI[Controller UI]
            P1[OCR Service]
            P2[Docling Service]
            P3[Chunker Service]
            P4[KG Builder]
            P5[Embed Service]
            P6[Retrieval Service]
            P7[GNN Service]
            P8[LLM Assistant Service]
        end
    end
    Blob[Azure Blob Storage]
    Neo4j[Neo4j Graph DB]
    Vector[Milvus / Qdrant]
    LLMAPI[Azure OpenAI / Foundry]
    CTRL -- Blob
    P4 -- Neo4j
    P5 -- Vector
    CTRL -- LLMAPI
```

