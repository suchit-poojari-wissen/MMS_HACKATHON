# Controller UI

## Purpose
Provide a lightweight web UI for uploads, job monitoring, artifact viewing and final report review.

## Views
- Upload page with file chooser and initial query field
- Job list (filterable)
- Job detail with stage timeline and logs
- Artifact viewer (JSON pretty-print + download)
- Final report view (assistant_response.json)

## Requirements
- Responsive UI, simple layout
- Use Controller API only; no direct calls to backend services
- Minimal auth (internal trusted network) for initial rollout

## Implementation notes
- React or static HTML + Alpine.js acceptable
- Use code syntax highlighting for JSON viewer
