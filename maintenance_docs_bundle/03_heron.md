
# Phase 1 – OCR & Layout Extraction (Docling Heron)

## Purpose
Use Docling Heron for OCR and layout extraction to convert scanned PDFs/images into structured layout-aware JSON.

## Inputs
- PDF, JPG, PNG, TIFF files
- Optional params: language, dpi_override, fast_mode

## Outputs
- Timestamped `heron_output_<ISO>.json` containing:
  - pages[]
  - blocks[] (text_line, table_candidate, image)
  - bounding boxes
  - OCR confidence
  - metadata: `duration_ms`, `dt_timestamp`, `layout_device`, `ocr_device`

## Example Output
```json
{
  "document_id": "DOC_0001",
  "pages": [
    {
      "page_number": 1,
      "blocks": [
        {
          "id": "b1",
          "type": "text_line",
          "bbox": [80, 120, 1400, 150],
          "text": "Compressor Fault Codes",
          "confidence": 0.98
        }
      ]
    }
  ]
}
```

## API Endpoints
POST /v1/process  
GET /v1/status/{job_id}  
GET /v1/result/{job_id}

## Configuration
- Env vars (examples):
  - `PHASE1_ARTIFACTS_DIR` (default `artifacts/ocr`)
  - `PHASE1_USE_STUB_OCR` (`true|false`)
  - `PHASE1_DEVICE_OCR` (`dml|cpu`) — ONNX Runtime DirectML on Windows or CPU fallback
  - `PHASE1_DEVICE_LAYOUT` (`gpu|cpu`) — optional hint when supported by Docling/PyTorch

## Requirements
- High OCR accuracy
- Deterministic output
- Compatible with Granite input schema
 - Persist artifacts per job with status and result retrieval
