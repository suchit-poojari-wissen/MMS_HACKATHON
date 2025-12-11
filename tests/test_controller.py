import pytest
import httpx
from jose import jwt
from controller_service.main import app

SECRET = "dev-secret-change-me"
ALGO = "HS256"


def make_token(roles):
    return jwt.encode({"roles": roles}, SECRET, algorithm=ALGO)


def auth_headers(roles):
    token = make_token(roles)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.mark.anyio
@pytest.mark.parametrize("endpoint,payload", [
    ("/jobs", {"source_path": "docs/sample.pdf", "language": "en"}),
    ("/incidents", {"title": "Test Incident", "severity": "low"}),
])
async def test_create_resources(endpoint, payload):
    headers = auth_headers(["operator"])  # operator allowed
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(endpoint, json=payload, headers=headers)
        assert r.status_code == 200, r.text


@pytest.mark.anyio
async def test_phase1_ocr():
    headers = auth_headers(["engineer"])  # engineer allowed
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/phase1/ocr", json={"source_path": "docs/sample.pdf", "language": "en"}, headers=headers)
        assert r.status_code == 200
        js = r.json()
        assert "text" in js and "blocks" in js


@pytest.mark.anyio
async def test_phase2_layout():
    headers = auth_headers(["engineer"])  # engineer allowed
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/phase2/layout", json={"text": "Title here. Body content goes here."}, headers=headers)
        assert r.status_code == 200
        js = r.json()
        assert "layout" in js


@pytest.mark.anyio
async def test_phase3_chunk():
    headers = auth_headers(["engineer"])  # engineer allowed
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/phase3/chunk", json={"text": "One. Two. Three."}, headers=headers)
        assert r.status_code == 200
        js = r.json()
        assert isinstance(js, list) and len(js) == 3


@pytest.mark.anyio
async def test_auth_required():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/jobs", json={"source_path": "x", "language": "en"})
        assert r.status_code == 401


@pytest.mark.anyio
async def test_health_and_version_public():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200
        r = await client.get("/version")
        assert r.status_code == 200
        js = r.json()
        assert "version" in js and "git_sha" in js and "db" in js and "build_time" in js and "env" in js
        r = await client.get("/healthz")
        assert r.status_code == 200


@pytest.mark.anyio
async def test_health_and_version_with_token():
    headers = auth_headers(["viewer"])  # any role acceptable
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health", headers=headers)
        assert r.status_code == 200
        r = await client.get("/version", headers=headers)
        assert r.status_code == 200
        r = await client.get("/healthz", headers=headers)
        assert r.status_code == 200


@pytest.mark.anyio
async def test_phase_endpoints_forbid_operator():
    headers = auth_headers(["operator"])  # operator no longer allowed for phases
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/phase1/ocr", json={"source_path": "x", "language": "en"}, headers=headers)
        assert r.status_code == 403
        r = await client.post("/phase2/layout", json={"text": "t"}, headers=headers)
        assert r.status_code == 403
        r = await client.post("/phase3/chunk", json={"text": "One. Two."}, headers=headers)
        assert r.status_code == 403
