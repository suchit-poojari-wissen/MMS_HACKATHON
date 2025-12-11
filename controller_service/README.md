KMS Controller Service (Phases 1–3)

Overview
- FastAPI service providing endpoints for Jobs, Incidents, and Phase 1–3 stubs (OCR, Layout, Chunking).
- SQLite persistence for Jobs and Incidents.

Quick Start
1) Create and activate a virtual environment (optional but recommended).
2) Install dependencies: `pip install -r requirements.txt`.
3) Run: `uvicorn controller_service.main:app --reload`.

Endpoints
- POST `/jobs` — create a job.
- POST `/incidents` — create an incident.
- POST `/phase1/ocr` — stub OCR, returns text + blocks.
- POST `/phase2/layout` — stub layout detection.
- POST `/phase3/chunk` — returns rule-based chunks.
 - GET `/health` — public health check.
 - GET `/version` — public version info, includes git SHA and DB status.
 - GET `/healthz` — public health check alias.

Version diagnostics
- Response includes:
	- `version`: app version string.
	- `git_sha`: current commit (short) if git available.
	- `build_time`: ISO UTC timestamp captured at app startup.
	- `env`: environment tag from `KMS_ENV` (default `dev`).
	- `db`: `{ status, url }` with connectivity check.

Configure environment tag:
- Set `KMS_ENV` before starting the server, e.g. (PowerShell):

```powershell
$env:KMS_ENV = "dev" # or "prod"
uvicorn controller_service.main:app --reload
```

Notes
- DB file: `kms_controller.db` (created in repo root).
- RBAC and JWT are stubs for now; to be integrated per PRs.

RBAC (tightened)
- `/jobs`, `/incidents`: roles `operator`, `admin` (+ `ingestor` for jobs, `supervisor` for incidents) allowed.
- Phase endpoints (`/phase1/ocr`, `/phase2/layout`, `/phase3/chunk`): roles `engineer`, `admin`.
- `/health`, `/version`: any authenticated role.
