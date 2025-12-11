# Phase 7 — GNN Reasoning Service (Optional)

## Purpose
Apply Graph Neural Networks to subgraphs to predict probable root causes, MTTR estimates, and rank diagnostic paths.

## Inputs
- `retrieved_context.json` (subgraph, node features, vector hits)
- Historical labelled repair cases for offline training

## Outputs
- `gnn_predictions.json` with ranked root causes, mttr estimate, confidences

## Example
```json
{
  "query_id":"q_123",
  "predictions":{"root_causes":[{"cause":"Sensor Misalignment","score":0.84}],"mttr_minutes":45},
  "model_version":"gnn_v0.1"
}
```

## Functional Requirements
- Offline training pipeline using PyTorch Geometric or DGL
- Model versioning and A/B testing
- Export optimized model for inference (TorchScript)

## Non-functional Requirements
- Inference latency target < 250 ms (GPU recommended)
- Training environment must be reproducible (Docker & GPU drivers)

## API
```
POST /predict
POST /train   # async
GET /model_status
GET /health
```

## Error handling
- MODEL_NOT_READY
- INSUFFICIENT_TRAIN_DATA
