# Phase 7 — GNN Reasoning Service PR

## Summary
- Purpose: Apply GNNs to subgraphs to predict probable root causes, MTTR, and rank diagnostic paths.
- Inputs: `retrieved_context.json` (subgraph, node features, vector hits); historical labelled repair cases for training.
- Outputs: `gnn_predictions.json` with ranked root causes, MTTR estimate, confidences.

## API
```
POST /predict
POST /train   # async
GET  /model_status
GET  /health
```

## Functional Requirements
- Offline training using PyTorch Geometric or DGL.
- Model versioning and A/B testing.
- Export optimized model for inference (TorchScript).

## Non-functional
- Inference latency < 250 ms (GPU recommended).
- Reproducible training env (Docker + GPU drivers).

## Example Output
```json
{
  "query_id":"q_123",
  "predictions":{"root_causes":[{"cause":"Sensor Misalignment","score":0.84}],"mttr_minutes":45},
  "model_version":"gnn_v0.1"
}
```

## Error Handling
- `MODEL_NOT_READY`.
- `INSUFFICIENT_TRAIN_DATA`.

## Observability
- `/health`; metrics: inference latency, model version usage, training job runtime.
 - Per-incident logging: record predictions and rationale to the Controller audit trail keyed by `incident_id`; include citations to KG nodes/edges.

## Testing Strategy
- Unit: feature construction, prediction ranking.
- Integration: `/predict` with Phase 6 context; `/train` lifecycle.
- Performance: GPU inference latency; A/B evaluation.

## Assumptions
- Graph features: degree, centrality, edge types, KG confidences; enriched with chunk scores.
- Deployment: single GPU node; batch predict up to 32 queries; model cache warm.
 - Context: consume Phase 6 subgraphs scoped by `source_path_prefix` and respect `language` metadata for bilingual handling.
 - RBAC: expose predictions only within the incident’s visibility; advisors can view but cannot trigger training jobs unless permitted.

## Additional Notes on GNN usage
AI/ML Capabilities and Limitations Without Sensor or High-Frequency Logs (With GNN Extensions)
Overview
• This document summarizes what Artificial Intelligence (AI), Machine Learning (ML), and Graph Neural Networks (GNNs) can and cannot do when only breakdown and fix history is available, without sensor data or high-frequency machine logs.
AI/ML Capabilities (What IS Possible Without Sensor Data)
• 1. Generate Initial Fault Tree Analysis (FTA) Structures:
•    - AI can infer cause–effect relationships from historical failures and maintenance actions.
•    - Can construct approximate FTA diagrams showing common root causes and failure paths.
•    - These FTAs are useful as a starting point for engineers.
• 2. Build an Operator Triage Bot:
•    - The bot can ask structured diagnostic questions based on symptoms.
•    - It can dynamically adapt questions like an expert technician.
•    - It can suggest likely faults based on similarity to past cases.
• 3. Diagnose Problems Using Maintenance History and Manuals:
•    - LLMs can read operator notes, OEM manuals, and past repairs.
•    - They can map symptoms to probable causes.
•    - They can provide recommended corrective actions.
• 4. Create a Self-Learning Knowledge Base:
•    - Each breakdown → fix cycle becomes training data.
•    - System improves fault prediction accuracy over time.
•    - Failure mode frequencies can be calculated and used to rank likely causes.
• 5. Automate Repair Ticket Generation:
•    - Triage bot can pre-fill root cause, recommended fix, spare parts needed.
•    - Helps reduce downtime and improves consistency.
• 6. Cluster and Categorize Historical Failures:
•    - AI can group similar breakdowns.
•    - Allows identification of recurring issues and chronic problem areas.
AI/ML Limitations (What is NOT Possible Without Sensor Data)
• 1. No Early Failure Detection:
•    - Without vibration, current, temperature, or acoustic logs, AI cannot detect faults before breakdown occurs.
• 2. Cannot Identify Physical Failure Signatures:
•    - Mechanical phenomena like bearing defects, misalignment, cavitation, or gear tooth cracks cannot be detected or classified.
• 3. Limited Causal Accuracy in FTA Trees:
•    - AI relies solely on textual history, which may be incomplete or inconsistent.
•    - Cannot confirm physical causation—only statistical associations.
• 4. Cannot Perform Remaining Useful Life (RUL) Estimation:
•    - No degradation trajectory can be modeled without time‑series sensor data.
• 5. No Ability to Assess Machine Health in Real-Time:
•    - AI cannot monitor trends or trigger alerts as no streaming data is available.
• 6. Limited Ability to Distinguish Between Similar Faults:
•    - If two issues share identical breakdown symptoms, AI cannot differentiate without sensor signatures.
Role of Graph Neural Networks (GNNs) in This Environment
• 1. Build a Failure Mode Graph (FMG):
•    - Using breakdown records, symptoms, causes, and fixes can be turned into graph nodes.
•    - GNNs learn relationships between symptoms, failure modes, and fixes.
• 2. Enhance Fault Tree Analysis (FTA):
•    - FTA is naturally a graph structure.
•    - GNNs refine FTA branches by learning which nodes frequently connect or cascade.
• 3. Improve Root-Cause Inference:
•    - Given operator inputs like 'vibration + overheating + slow cycle', GNNs propagate signals across connected nodes.
•    - This improves accuracy over traditional ML approaches.
• 4. Identify Hidden Failure Pathways:
•    - GNNs detect intermediate failure steps missing from textual logs.
•    - Helps uncover cascading failure patterns.
• 5. Recommend Highly Relevant Fixes:
•    - GNN attention mechanisms identify which past fixes resolved similar graph structures.
• 6. Enable a Hybrid LLM + GNN Diagnostic System:
•    - LLM interprets operator descriptions.
•    - GNN ranks likely root causes.
•    - Combined system mimics expert reasoning.
• 7. Limitations of GNNs:
•    - Cannot detect physical signatures without sensor data.
•    - Require enough historical records to construct meaningful graphs.
•    - Need normalization of terminology (e.g., 'overload trip' vs 'OL trip').
Recommended Architecture Including GNNs
• 1. Data Layer:
•    - Breakdown history, maintenance notes, operator input, OEM manuals.
• 2. Knowledge Graph:
•    - Nodes: symptoms, causes, fixes, machine subsystems.
•    - Edges: symptom→cause, cause→fix, subsystem→component.
• 3. GNN Layer:
•    - Learns failure propagation, hidden pathways, and diagnosis probabilities.
• 4. LLM Reasoning Layer:
•    - Handles conversational triage, question generation, documentation, and initial FTA construction.
• 5. Output Layer:
•    - Ranked diagnosis list.
•    - Suggested repair actions.
•    - Improved FTA diagrams.
•    - Auto-filled maintenance tickets.
Summary
• GNNs significantly enhance AI/ML capabilities by modeling relational structures between symptoms, causes, and fixes.
• Even without sensor logs, combining LLMs + GNNs provides a powerful diagnostic, triage, and FTA-building capability.
• Sensor data would further improve accuracy, but is not required to benefit from GNN reasoning.

## Implementation Notes (Features derived from Additional Notes)
- Canonical graph schema: nodes {Symptom, FailureMode, Fix, Subsystem, Component}; edges {symptom→cause, cause→fix, subsystem→component}.
- Feature set:
  - Node: type one-hot, degree/centrality, historical occurrence frequency, KG confidence, chunk similarity scores.
  - Edge: type one-hot, co-occurrence counts, time-gap statistics, provenance weight.
  - Query features: embedded symptom text, resolved entities, vector hit scores.
- Normalization: synonym dictionary and alias index (e.g., "overload trip" ≡ "OL trip"); text normalization before graph updates.
- Training data hygiene: de-duplicate near-identical cases; minimum support threshold before a cause appears in top-k.
- Inference inputs: Phase 6 subgraph + vector-hit features + KG confidences + operator observations as sparse indicators.
- Scoring policy: calibrate scores; gate low-confidence predictions; expose top-k with confidence bands and rationale.
- Evaluation: offline metrics (precision@k, MTTR MAE); A/B tests against prior model versions; dataset snapshot versioning.

