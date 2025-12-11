import pytest
import httpx
from phase1_ocr_service.main import app


@pytest.mark.anyio
async def test_health():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200


@pytest.mark.anyio
async def test_process_stub_mode(monkeypatch):
    monkeypatch.setenv("PHASE1_USE_STUB_OCR", "true")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/v1/process", json={"source_path": "docs/sample.pdf", "language": "en", "dpi_override": 300, "fast_mode": False})
        assert r.status_code == 200
        js = r.json()
        assert "job_id" in js and "artifact" in js
