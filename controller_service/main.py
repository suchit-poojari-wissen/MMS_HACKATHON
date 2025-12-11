from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from .db import init_db, SessionLocal, SQLALCHEMY_DATABASE_URL, engine
from . import models
from .schemas import JobCreate, JobOut, IncidentCreate, IncidentOut, OCRInput, LayoutInput, ChunkInput, ChunkOut
from sqlalchemy.orm import Session
from .auth import get_current_roles, require_roles
import subprocess
import os
from datetime import datetime, UTC
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs("logs", exist_ok=True)
    app.state.build_time = datetime.now(UTC).isoformat()
    yield


app = FastAPI(title="KMS Controller", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




# Jobs
@app.post("/jobs", response_model=JobOut)
def create_job(job: JobCreate, db: Session = Depends(get_db), _: None = Depends(require_roles(["operator", "admin", "ingestor"]))):
    db_job = models.Job(source_path=job.source_path, language=job.language)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    out = JobOut(id=db_job.id, source_path=db_job.source_path, language=db_job.language, status=db_job.status)
    log_event("jobs:create", out.model_dump())
    return out


# Incidents
@app.post("/incidents", response_model=IncidentOut)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db), _: None = Depends(require_roles(["operator", "admin", "supervisor"]))):
    db_inc = models.Incident(title=incident.title, severity=incident.severity)
    db.add(db_inc)
    db.commit()
    db.refresh(db_inc)
    out = IncidentOut(id=db_inc.id, title=db_inc.title, severity=db_inc.severity, status=db_inc.status)
    log_event("incidents:create", out.model_dump())
    return out


# Phase 1: OCR
@app.post("/phase1/ocr")
def phase1_ocr(payload: OCRInput, _: None = Depends(require_roles(["engineer", "admin"]))):
    # Stub: simulate OCR text extraction
    text = f"[OCR simulated] from {payload.source_path} ({payload.language})"
    result = {"text": text, "blocks": [{"type": "paragraph", "text": text}]}
    log_event("phase1:ocr", {"source_path": payload.source_path, "language": payload.language, "result": result})
    return result


# Phase 2: Layout
@app.post("/phase2/layout")
def phase2_layout(payload: LayoutInput, _: None = Depends(require_roles(["engineer", "admin"]))):
    # Stub: simulate layout detection
    layout = [
        {"id": 1, "type": "title", "text": payload.text[:50]},
        {"id": 2, "type": "body", "text": payload.text[50:200]},
    ]
    result = {"layout": layout}
    log_event("phase2:layout", {"result": result})
    return result


# Phase 3: Chunking
@app.post("/phase3/chunk", response_model=List[ChunkOut])
def phase3_chunk(payload: ChunkInput, _: None = Depends(require_roles(["engineer", "admin"]))):
    # Simple rule-based chunking for now
    text = payload.text.strip()
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    chunks = []
    for idx, s in enumerate(sentences):
        chunks.append(ChunkOut(index=idx, content=s))
    log_event("phase3:chunk", {"count": len(chunks)})
    return chunks


def log_event(event: str, data: dict):
    try:
        line = f"{datetime.now(UTC).isoformat()}\t{event}\t{data}\n"
        with open(os.path.join("logs", "controller.log"), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


# Health and Version (require token presence but no specific role)
@app.get("/health")
def health():
    ok = "ok"
    try:
        conn = engine.connect()
        conn.close()
    except Exception:
        ok = "db_error"
    return {"status": ok}


@app.get("/version")
def version():
    git_sha = None
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        if res.returncode == 0:
            git_sha = res.stdout.strip()
    except Exception:
        git_sha = None
    db_status = "ok"
    try:
        conn = engine.connect()
        conn.close()
    except Exception:
        db_status = "db_error"
    env = os.getenv("KMS_ENV", "dev")
    return {
        "version": app.version,
        "git_sha": git_sha,
        "build_time": getattr(app.state, "build_time", None),
        "env": env,
        "db": {"status": db_status, "url": SQLALCHEMY_DATABASE_URL},
    }


@app.get("/healthz")
def healthz():
    ok = "ok"
    try:
        conn = engine.connect()
        conn.close()
    except Exception:
        ok = "db_error"
    return {"status": ok}

