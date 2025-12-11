Phase 1 — OCR & Layout (Docling Heron) Service

Overview
- Standalone FastAPI service implementing `/v1/process`, `/v1/status/{job_id}`, `/v1/result/{job_id}`, `/health`.
- Uses Docling + Heron via Python SDK to perform OCR + layout; persists artifacts to `artifacts/ocr/<job_id>/`.
 - Outputs include per-run timestamps and metadata (duration, device hints).

Install & Run (PowerShell)
```powershell
Set-Location D:\Documents\GitHub\KMS
python -m venv .venv
 .\.venv\Scripts\Activate.ps1
pip install -r .\phase1_ocr_service\requirements.txt
uvicorn phase1_ocr_service.main:app --reload
```

Process Example
```powershell
$body = @{ source_path = "https://arxiv.org/pdf/2408.09869"; language = "ja"; dpi_override = 300; fast_mode = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/process -ContentType "application/json" -Body $body
```

Config (env vars)
- `PHASE1_MAX_PAGES_SYNC` (default `10`)
- `PHASE1_CONFIDENCE_THRESHOLD` (default `0.65`)
- `PHASE1_ARTIFACTS_DIR` (default `artifacts/ocr`)
- `PHASE1_USE_STUB_OCR` (default `false`; set `true` to simulate OCR)
 - `PHASE1_DEVICE_OCR` (optional: `dml|cpu`) — ONNX Runtime DirectML for OCR on Windows or CPU fallback
 - `PHASE1_DEVICE_LAYOUT` (optional: `gpu|cpu`) — hint for layout device where supported

Notes
- Artifacts: timestamped `heron_output_<ISO>.json` and optional assets.
- Large docs: initial implementation runs sync; status/result endpoints support polling and retrieval.