# Docling Acceleration and Controller Viewer Plans

## 1) Docling Acceleration (General GPU/DML)

Goal: Reduce end-to-end OCR/layout time by leveraging widely available GPU acceleration paths (PyTorch GPU where supported and ONNX Runtime DirectML on Windows), while keeping output parity with the current Docling pipeline.

Summary of constraints and opportunities:
- Docling pipeline uses PDF parsing + OCR + layout modeling. OCR engines supported: auto, rapidocr (torch/onnxruntime), tesseract, easyocr. Layout models typically use Hugging Face transformers; acceleration usually via PyTorch GPU or ONNX Runtime (DirectML on Windows).
- Not all Docling models have ONNX exports out of the box; the best practical path is accelerating OCR components (RapidOCR ONNX) and selectively optimizing layout where supported.

Key model candidates and suggested accelerators:
- Layout analysis (Docling Layout Heron / vision-transformer backbones): Prefer GPU acceleration where officially supported by Docling/PyTorch; otherwise run on CPU with threading.
- OCR text detection/recognition (RapidOCR PP-OCRv4): Prefer ONNX Runtime with DirectML on Windows for broad GPU support; fall back to Torch CPU/Tensor cores when ONNX is unavailable.
- Table detection/structure extraction and lightweight classifiers: Use ONNX Runtime where models are available; otherwise CPU execution with vectorized NumPy.

Phased plan:
- Phase A: Baseline acceleration via ONNX Runtime DirectML
  - Use RapidOCR ONNX models with `onnxruntime-directml` on Windows to enable GPU acceleration without device-specific tooling.
  - Integrate via Docling plugin overrides or engine selection to ensure OCR runs on ORT.
  - Validate parity on a small suite; measure throughput.

- Phase B: Optional PyTorch GPU acceleration (where supported)
  - If layout models expose GPU-compatible paths, enable PyTorch GPU and optional mixed precision where safe.
  - Maintain CPU fallback and deterministic seeds.

- Phase C: System-level tuning
  - Enable HF model caching on fast storage, pre-warm caches, and batch page processing where feasible.
  - Add timing logs around conversion phases; persist metrics to artifacts for run-to-run comparison.

Actionable steps and commands:
- Install ONNX Runtime DirectML on Windows:
  ```powershell
  D:/Documents/GitHub/KMS/.venv/Scripts/python.exe -m pip install onnxruntime-directml
  ```
- Configure Docling to prefer ONNX OCR when available:
  - `PHASE1_DEVICE_OCR=dml` to indicate DirectML usage for OCR.
  - `PHASE1_FAST_MODE=true` and `PHASE1_ENABLE_MIXED_PRECISION=true` as optional tuning flags (where applicable).

Code hooks:
- For ONNX paths, define an inference wrapper using `onnxruntime.InferenceSession(providers=['DmlExecutionProvider'])` and log the selected providers for visibility.
- For PyTorch paths (if used), prefer generic GPU settings and avoid device-specific assumptions; always keep a CPU fallback.

Risks and mitigations:
- Model compatibility with ONNX may require opset conversions; keep a CPU fallback.
- Maintain deterministic seeds and document any precision changes when enabling mixed precision.

Success criteria:
- 2x speedup on multi-page documents using ONNX Runtime DirectML; stable outputs within acceptable variance.

## 2) Controller UI Viewer with Bounding-Box Citations and Filters

Goal: Build a UI in the Controller to show source PDF on the left and extracted elements on the right, with bounding-box highlights on the PDF when items are selected; multi-select filters to choose which elements to display (Doc Title, Page Header, Section Header, Table Header, etc.).

Architecture overview:
- Backend (Controller service):
  - Endpoint to fetch processed Docling artifacts (`heron_output.json`, optional per-page boxes/assets).
  - Endpoint to fetch rendered PDF pages as images (server-side rendering via `pdfium` or client-side via PDF.js).
- Frontend (Controller UI):
  - Left pane: PDF viewer (PDF.js) with ability to overlay SVG layers for bounding boxes.
  - Right pane: Extracted elements list with filters (checkboxes) and search; clicking entries scrolls/zooms PDF and highlights corresponding boxes.

Data model:
- `heron_output.json` should contain per-element:
  - `id`, `type` (doc_title, page_header, section_header, table_header, figure_caption, etc.), `page_index`, `bbox` (x,y,w,h in page coordinates), `text`, `confidence`.
- Optional per-page assets: width/height, scale info.

Backend endpoints:
- `GET /docs/{job_id}/manifest` → lists available artifacts.
- `GET /docs/{job_id}/elements?types=doc_title,section_header,...` → returns filtered elements with bboxes.
- `GET /docs/{job_id}/pages/{page}/image` → returns PNG/JPEG of the page.
- `GET /docs/{job_id}/pages/{page}/boxes?types=...` → returns overlay boxes for quick rendering.

Frontend implementation plan:
- Use PDF.js to render pages; maintain a per-page scale factor.
- Overlay an absolutely positioned SVG layer; draw rectangles for each element’s bbox transformed to viewport scale.
- Filters panel:
  - Multiselect checkboxes: Doc Title, Page Header, Section Header, Table Header, Figure Caption, Table Caption, Footer, List Item, Equation.
  - Apply on client side; fetch all and filter locally, or query server with `types`.
- Interactions:
  - Clicking an element highlights its box on the page; auto-scroll to its page.
  - Hovering a box shows tooltip with `type`, `text`, `confidence`.

Tech stack:
- Frontend: React + PDF.js, Tailwind/Chakra for UI components.
- Backend: FastAPI endpoints added to Controller; minor schema to serve elements.

Step-by-step:
1. Normalize `heron_output.json` in Phase 1 to include `elements` array with the fields above.
2. Add Controller API routes to serve elements and page images.
3. Build UI component `PdfWithOverlays`:
   - Renders PDF pages via PDF.js
   - Exposes method `highlightElement(elementId)`
4. Build `ElementsPanel` with multiselect filters.
5. Wire selection to highlight and scroll.
6. Add simple caching for page images; lazy-load as the user scrolls.

Bounding box coordinate handling:
- Store `bbox` in PDF page coordinate space (points). On render, map to viewport via `scale`.
- Handle rotation if pages are rotated; PDF.js provides transform matrices.

Accessibility and performance:
- Debounce filter changes; virtualize element list for large docs.
- Use canvas layering to minimize reflows; offscreen canvas for image processing.

Deployment:
- Controller serves static frontend; endpoints under `/viewer/*` and `/docs/*`.

Success criteria:
- Smooth viewing and accurate highlights; fast filter and navigation.

Next steps:
- Confirm `heron_output.json` schema and, if needed, add a Phase 1 post-processor to extract headers/sections and bboxes from Docling output.
- I can scaffold the Controller viewer routes and a React page to prototype this.
