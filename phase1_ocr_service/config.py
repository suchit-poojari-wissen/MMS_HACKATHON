import os

MAX_PAGES_SYNC = int(os.getenv("PHASE1_MAX_PAGES_SYNC", "10"))
CONFIDENCE_THRESHOLD = float(os.getenv("PHASE1_CONFIDENCE_THRESHOLD", "0.65"))
ARTIFACTS_DIR = os.getenv("PHASE1_ARTIFACTS_DIR", "artifacts/ocr")
USE_STUB_OCR = os.getenv("PHASE1_USE_STUB_OCR", "false").lower() == "true"
