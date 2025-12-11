from pydantic import BaseModel
from typing import Optional


class JobCreate(BaseModel):
    source_path: str
    language: Optional[str] = None


class JobOut(BaseModel):
    id: int
    source_path: str
    language: Optional[str] = None
    status: str


class IncidentCreate(BaseModel):
    title: str
    severity: str


class IncidentOut(BaseModel):
    id: int
    title: str
    severity: str
    status: str


class OCRInput(BaseModel):
    source_path: str
    language: Optional[str] = None
    dpi_override: Optional[int] = 300
    fast_mode: Optional[bool] = False


class LayoutInput(BaseModel):
    text: str


class ChunkInput(BaseModel):
    text: str


class ChunkOut(BaseModel):
    index: int
    content: str
