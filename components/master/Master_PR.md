# Maintenance Management System (MMS) — Master PR

## Overview
- Goal: Build a single-tenant, enterprise-grade MMS that ingests ~80k maintenance documents and hundreds of historic maintenance reports once, then handles sporadic updates and new maintenance reports. The system produces structured knowledge, searchable embeddings, graph intelligence, hybrid retrieval, and a grounded LLM assistant with a simple controller UI.
- Architecture: 8 phased services coordinated by a Controller, with consolidated APIs and a lightweight UI. Storage uses local dockerized components during development and will use blob + SQL/Cosmos in production; KG in Neo4j; vectors in VectorXDB. Security via internal trusted network and local mkcert certificates in Development, and Azure AD/OIDC for production if needed.

## Components
- `Controller`: Orchestration, job lifecycle, artifacts, status APIs; single-tenant auth assumptions; rate/concurrency tuned for bulk ingest then steady state.
- `Phase 1 — Heron OCR/Layout`: Docling Heron extracts layout-aware blocks to `heron_output.json`; params assumed (language=ja, dpi=300, fast_mode=false). Deterministic.
- `Phase 2 — Granite Structure`: Docling Granite converts Heron output to `docling_output.json` (sections, tables, figures, confidence). Deterministic, table F1 target.
- `Phase 3 — Chunking`: Converts structured elements to NDJSON chunks and manifest; windowing/overlap rules; VectorXDB ingestion assumptions (namespace, metadata, batch upserts, dedup).
- `Phase 4 — KG Builder`: Builds Neo4j KG with hybrid extraction and MERGE idempotency; provenance on edges; canonical IDs.
- `Phase 5 — Embeddings`: Generates embeddings and stores vectors in VectorXDB; metadata filters; search latency targets; upsert semantics.
- `Phase 6 — Hybrid Retrieval`: Fuses vector hits + KG subgraphs; entity resolution; explainability; latency target.
- `Phase 7 — GNN`: Predicts root causes/MTTR on subgraphs; training/inference pipeline; GPU suggested.
- `Phase 8 — LLM Assistant`: Produces grounded diagnostic guidance with citations; JSON schema validation; clarify loop.
 - `Controller UI`: Minimal web UI for upload, monitoring, artifacts, and final report, and a chatbot console for Phases 6/7/8 (query, prediction, diagnose) with streaming responses and citations.
- `Consolidated APIs`: Uniform endpoint definitions and error model across phases.

## Cross-Cutting Policies
- Auth: Internal trusted network; optional Azure AD/OIDC for UI. Key Vault for secrets.
- Rate Limits: Conservative defaults during bulk ingest; lower in steady state.
- Concurrency: System caps tuned for single-tenant; per-stage worker limits documented.
- Determinism: Phases 1–3 emphasize deterministic outputs; idempotent upserts in KG and embeddings.
- Observability: `/health` endpoints; metrics for throughput, latencies, errors; explainability attached where relevant.
 - Language support: End-to-end bilingual handling (English/Japanese). Capture `language` metadata on ingestion; bilingual tokenization, embeddings, retrieval, and LLM responses.

## Incident Lifecycle, State Durability, and Audit Trail
- States: `open` → `in-progress` → `awaiting-shift-handover` → `resolved` → `archived`. Allow `reopened` with rationale.
- Durability: Persist incident record, chat transcripts, artifacts, and decisions in durable storage (SQL/Cosmos for metadata; blob for large artifacts). All writes are idempotent and append-only for audit.
- Audit Trail: Immutable sequence of events with actor (`userId`, role), timestamp, action type, payload hash, and references to artifacts/citations. No destructive updates; corrections logged as new events.
- Shift Handover: Dedicated handover notes and checklist captured before state transition; include current hypotheses, pending tests, and next actions. Enforce required fields via schema validation.
- Remote Advisors: Role-based visibility and participation for external advisors. Advisors can subscribe to incidents, view timeline, propose actions, and attach citations. Access via secure links and time-bounded tokens.
- RBAC: Roles include `operator`, `supervisor`, `engineer`, `advisor`, `admin`. Endpoint-level authorization enforced in Controller; LLM Assistant adheres to incident visibility context.
- Observability: Per-incident metrics (time-to-first-response, time-in-state, handover completeness score), and audit consistency checks.

## Build Sequence Addendum (Incident Management)
- Extend Controller first to support incident CRUD, update, handover, advisor management, and audit.
- UI adds Incident Timeline and Handover views early to enable end-to-end validation.
- LLM Assistant adopts per-incident conversation state and produces handover summaries.

## Consistency & Contradiction Check
- Input/Output chaining: Heron → Granite → Chunking → KG/Embeddings → Retrieval → LLM is consistent. Phase 2 expects `heron_output.json` (aligned). Phase 3 references `docling_output.json` (aligned). Phase 5 uses `chunks.jsonl` (aligned). Phase 6 consumes vectors + KG (aligned). Phase 8 consumes retrieval and optional GNN outputs (aligned).
- API surface: Matches consolidated APIs; Controller endpoints consistent with UI usage.
- Terminology: Heron/Granite naming unified; chunk metadata keys consistent; canonical IDs (e.g., `Error:E47`).
- Fixed issue: Removed duplicate Outputs line in `3_Chunking_PR.md`.
- Assumptions: Clearly marked (Heron params, VectorXDB, weighting). No unresolved hard contradictions identified.

## Build Sequence (Strict)
1. Controller (core scaffolding, job lifecycle, artifact storage; minimal UI stub)
2. Phase 1 — Heron OCR/Layout (standalone service + API)
3. Phase 2 — Granite Structure (consume Heron; emit `docling_output.json`)
4. Phase 3 — Chunking (consume Granite; emit chunks + manifest)
5. Phase 5 — Embeddings (vector DB provisioning; ingest chunks; search API)
6. Phase 4 — KG Builder (ingest chunks to Neo4j; canonicalization + provenance)
7. Phase 6 — Hybrid Retrieval (fuse embeddings + KG; explainability)
8. Phase 7 — GNN (training/inference service)
9. Phase 8 — LLM Assistant (grounded outputs; clarify loop)
10. Controller UI (views wired to Controller APIs)
11. Consolidated APIs (OpenAPI docs; error model finalized)

Rationale:
- Build ingestion and structure first (1–4), then embeddings (5), then KG (6) to support hybrid retrieval (7). LLM assistant last to ensure grounded outputs. UI can be parallelized but finalized after Controller and core APIs.

## Interactive Diagnostic Capabilities (Phases 6–8)
- Diagnose incidents: produce probable root causes ranked with explainability.
- Suggest diagnostic confirmation tests to validate hypotheses.
- List top 3–5 FTA trees with suggested fixes for human review and refinement.
- Plan spares: list/order spares required for top 5 FTAs and corresponding fixes.
- Walkthrough guidance: step-by-step diagnostics and fixes for Maintenance Engineer.
- Confirmatory tests: suggest and record fix confirmatory tests with outcomes.
- Final Maintenance Record (MR): generate structured report for ME sign-off.
- Reinforcement learning: ingest MR into history to improve future MMS reasoning.

## Ready-to-Program Checklist
- Repo structure created under `components/*` with numbered PRs.
- Assumptions documented; open questions manageable (auth specifics, thresholds, limits).
- No blocking contradictions; data flow well-defined; APIs consistent.
- Next actionable step: Scaffold Controller service and minimal `/upload`, `/status`, `/run_stage`, `/artifact` endpoints.

## Open Questions (to refine during implementation)
- Exact confidence thresholds (OCR fallback; table acceptance).
- Embedding model/version and provider SLAs.
- KG canonicalization rules per domain specifics.
- Retrieval weighting coefficients per customer tuning.
- UI auth behind reverse proxy vs SSO.
