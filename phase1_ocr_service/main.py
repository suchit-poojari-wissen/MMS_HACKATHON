from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, UTC
from pathlib import Path
import os
import hashlib
import time

from .config import MAX_PAGES_SYNC, CONFIDENCE_THRESHOLD, ARTIFACTS_DIR

app = FastAPI(title="Phase1 OCR Service", version="0.1.0")


class ProcessInput(BaseModel):
    source_path: str
    language: Optional[str] = "ja"
    dpi_override: Optional[int] = 300
    fast_mode: Optional[bool] = False


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def compute_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/process")
def process(payload: ProcessInput):
    # Optional acceleration: prefer Intel Arc via PyTorch XPU if requested
    accel = os.getenv("PHASE1_DEVICE_LAYOUT", "").lower()
    ocr_accel = os.getenv("PHASE1_DEVICE_OCR", "").lower()
    if accel == "xpu":
        try:
            import torch
            if hasattr(torch, "xpu") and torch.xpu.is_available():
                # Set default device to XPU so downstream Torch-based libs favor GPU
                if hasattr(torch, "set_default_device"):
                    torch.set_default_device("xpu")
            else:
                pass
        except Exception:
            pass
    src = payload.source_path
    now_iso = datetime.now(UTC).isoformat()
    job_id = hashlib.md5(f"{src}-{now_iso}".encode()).hexdigest()[:12]
    out_dir = Path(ARTIFACTS_DIR) / job_id
    ensure_dir(out_dir)

    use_stub = os.getenv("PHASE1_USE_STUB_OCR", "false").lower() == "true"
    if use_stub:
        # Simulated output
        result = {
            "document_id": job_id,
            "pages": [
                {"index": 0, "blocks": [{"type": "text_line", "text": f"OCR stub for {src}"}]}
            ],
            "metadata": {
                "language": payload.language,
                "dpi": payload.dpi_override,
                "confidence": 0.99,
                "fast_mode": payload.fast_mode,
            },
        }
        result["metadata"]["dt_timestamp"] = now_iso
        out_file = out_dir / f"heron_output_{now_iso.replace(':','-')}".replace("/","-")
        out_file = out_file.with_suffix(".json")
        out_file.write_text(str(result), encoding="utf-8")
        return {"job_id": job_id, "artifact": str(out_file), "summary": {"pages": 1}}

    try:
        # Use Docling DocumentConverter
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        t0 = time.time()
        conv = converter.convert(src)
        t1 = time.time()
        # Export optional assets (guard for docling version differences)
        assets_zip = None
        pages_count = None
        if hasattr(conv, "assets") and conv.assets is not None:
            assets_zip = out_dir / "heron_assets.zip"
            try:
                conv.assets.save(assets_zip)
                pages_count = len(conv.assets.pages) if getattr(conv.assets, "pages", None) else None
            except Exception:
                assets_zip = None
        # Persist combined JSON with minimal fields for Heron-style output
        doc_obj = getattr(conv, "document", None)
        doc_dict = doc_obj.export_to_dict() if doc_obj is not None else getattr(conv, "to_dict", lambda: {} )()
        output = {
            "document_id": job_id,
            "pages": pages_count,
            "document": doc_dict,
            "metadata": {
                "language": payload.language,
                "dpi": payload.dpi_override,
                "fast_mode": payload.fast_mode,
                "source_path": src,
                "layout_device": accel or None,
                "ocr_device": ("dml" if ocr_accel == "dml" else None),
                "duration_ms": int((t1 - t0) * 1000),
                "dt_timestamp": now_iso,
            },
        }
        out_file = out_dir / f"heron_output_{now_iso.replace(':','-')}".replace("/","-")
        out_file = out_file.with_suffix(".json")
        out_file.write_text(
            __import__("json").dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        resp = {
            "job_id": job_id,
            "artifact": str(out_file),
            "summary": {"pages": pages_count},
        }
        if assets_zip:
            resp["assets"] = str(assets_zip)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR_ENGINE_ERROR: {e}")


_JOBS: Dict[str, Dict] = {}


@app.get("/v1/status/{job_id}")
def status(job_id: str):
    out_dir = Path(ARTIFACTS_DIR) / job_id
    if (out_dir / "heron_output.json").exists():
        return {"job_id": job_id, "state": "completed"}
    return {"job_id": job_id, "state": "unknown"}


@app.get("/v1/result/{job_id}")
def result(job_id: str):
    out = Path(ARTIFACTS_DIR) / job_id / "heron_output.json"
    if not out.exists():
        raise HTTPException(status_code=404, detail="Result not found")
    import json
    return json.loads(out.read_text(encoding="utf-8"))
