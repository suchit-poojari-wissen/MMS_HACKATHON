# Controller Orchestrator

## Purpose
Coordinate the pipeline end-to-end, manage job lifecycle, store artifacts, and present status to UI.

## API (summary)
```
POST /upload    # returns job_id
GET /status/{job_id}
POST /run_stage  # body: {job_id, stage_name, options}
GET /artifact/{job_id}/{artifact_name}
```
## Job lifecycle
- queued -> running -> success | failed
- per-stage status and logs retained
- artifacts persisted to blob storage with content hashes

## Functional Requirements
- Support retries, skip-to-stage, force-reprocess
- Provide per-stage timeouts and resource constraints
- Persist metadata in Azure SQL / COSMOS (prod) or SQLite (dev)

## Observability
- Job metrics, per-stage latencies, failure reasons
