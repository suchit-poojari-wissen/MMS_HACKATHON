# Current Development Status

## Phase 1 – OCR & Layout Service
- Endpoints: `/v1/process`, `/v1/status/{job_id}`, `/v1/result/{job_id}`, `/health`.
- Artifacts: timestamped `heron_output_<ISO>.json` per job under `artifacts/ocr/<job_id>/`.
- Metadata persisted: `duration_ms`, `dt_timestamp`, `layout_device`, `ocr_device`.
- Config (env): `PHASE1_ARTIFACTS_DIR`, `PHASE1_USE_STUB_OCR`, `PHASE1_DEVICE_OCR` (`dml|cpu`), `PHASE1_DEVICE_LAYOUT` (`gpu|cpu`).
- Stub mode: available via `PHASE1_USE_STUB_OCR=true` for fast testing.

## Acceleration (Device-Agnostic)
- OCR: supports ONNX Runtime DirectML on Windows (`PHASE1_DEVICE_OCR=dml`).
- Layout: uses CPU/GPU hints where supported; keeps CPU fallback.
- Mixed precision and further tuning planned; device-specific details omitted.

## Runner & Tests
- Local runner script executes Phase 1 against a given PDF and saves artifacts.
- Tests cover health and stub-mode; output persistence validated.

## Documentation
- `phase1_ocr_service/README.md`: service usage, endpoints, env flags, artifacts.
- `maintenance_docs_bundle/phase1_heron.md`: outputs, metadata, configuration.
- `maintenance_docs_bundle/12_apis.md`: Phase 1 API aligned to `/v1/*` + `/health`.
- `research/plans/docling_accel_and_viewer.md`: generalized acceleration plan and Controller Viewer plan.

## Next Steps
- Verify OCR provider logging at runtime (DirectML selection visibility).
- Optional: add per-phase timing (layout vs OCR vs table) and mixed precision toggles.
- Controller UI viewer scaffolding for bbox overlays and filters.