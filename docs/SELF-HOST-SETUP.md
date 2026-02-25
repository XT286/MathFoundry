# Self-Host Setup (MathFoundry MVP)

This setup targets one rented server (32GB RAM / 500GB disk) with bounded storage.

## 1) Prerequisites
- Docker + Docker Compose plugin
- Git

## 2) Clone and configure
```bash
git clone https://github.com/XT286/MathFoundry.git
cd MathFoundry
cp .env.example .env
```

Edit `.env` as needed:
- `MATHFOUNDRY_ARXIV_CATEGORY=math.AG`
- `MATHFOUNDRY_MAX_RAW_FILES=200`
- `MATHFOUNDRY_MAX_RESULTS_PER_INGEST=100`

## 3) Start stack
```bash
docker compose -f deploy/docker-compose.selfhost.yml up -d --build
```

## 4) Verify
```bash
curl http://localhost:8000/health
```

## 5) Run one manual ingest now
```bash
docker compose -f deploy/docker-compose.selfhost.yml exec api python scripts/ingest_arxiv_math_ag.py
```

## 6) Storage control
Raw XML files are kept under `data/raw`. The ingest script auto-prunes old files by `MATHFOUNDRY_MAX_RAW_FILES`.

## 7) Stop stack
```bash
docker compose -f deploy/docker-compose.selfhost.yml down
```
