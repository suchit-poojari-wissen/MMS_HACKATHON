# KMS Third-Party Starters

This folder contains helper scripts to fetch recommended repositories and run core infrastructure locally.

## Clone repos

Run from PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
./third_party/clone_repos.ps1
```

Repos will be placed under `third_party/repos`.

## Docker Compose (ready, but optional to run)

The `docker-compose.yml` at the repo root is ready for local services, but you do not need to start anything now.

When you choose to run later:

```powershell
docker compose up -d

# Check logs
docker compose logs -f neo4j
docker compose logs -f chromadb
```

Services configured:
- Neo4j Community on `http://localhost:7474`, Bolt `7687` (user `neo4j`, pass `password`)
- ChromaDB on `http://localhost:8000`
- Docling Heron on `http://localhost:8081`
- Docling Granite on `http://localhost:8082`
- GraniteRAG on `http://localhost:8083`
- NGINX reverse proxy on `http://localhost/` (optional)

## Notes
- Ports and credentials are for local development only; change before production.
- Use volumes to persist data between restarts.
- When VectorXDB details are available, swap `chromadb` service to your VectorXDB image and ports.

<!-- Phase-to-Repo Usage Map moved to maintenance_docs_bundle/starter_code (1).md -->
