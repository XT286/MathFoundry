# MathFoundry System Requirements and Cost Options

Last updated: 2026-02-22

This document compares two deployment approaches:

1. **Self-host on your own server**
2. **Managed third-party hosting**

For each approach, it provides requirements and cost breakdown for:
- **MVP** (algebraic geometry first, low-to-moderate usage)
- **Full scale** (whole arXiv math focus, higher usage)

---

## Assumptions

- Primary use case: citation-grounded QA over arXiv math papers.
- LLM inference is external API for quality/stability in both options (initially).
- Costs are rough order-of-magnitude estimates, not quotes.

---

## Option A — Self-host (your own server)

## A1) MVP (math.AG first)

### Recommended server requirements
- CPU: 8 vCPU
- RAM: 32 GB
- Disk: 1 TB NVMe SSD
- Network: stable broadband, low packet loss
- OS: Ubuntu 22.04+ (or equivalent Linux)

### Services on server
- API service (FastAPI)
- Worker (ingestion/indexing jobs)
- Postgres (+ pgvector)
- Optional: local object store path + periodic backup sync

### MVP monthly cost breakdown (self-host)
- Server/VPS: ~$40–$150
- Backups/object storage: ~$5–$30
- Domain/TLS/misc: ~$0–$10
- LLM + embeddings API usage: ~$50–$150
- Monitoring/logging tools (lean): ~$0–$20

**Estimated total (MVP self-host): ~$95–$360 / month**

### Notes
- Lowest infra subscription cost, higher ops burden.
- You are responsible for patching, backups, uptime, recovery.

---

## A2) Full scale (whole arXiv math + higher traffic)

### Recommended server requirements
- CPU: 16–32 vCPU
- RAM: 64–128 GB
- Disk: 2–4 TB NVMe SSD
- Optional: second node for redundancy/search separation

### Full-scale monthly cost breakdown (self-host)
- Primary server: ~$150–$500
- Optional secondary/replica: +$100–$400
- Backups/object storage: ~$20–$100
- LLM + embeddings API usage: ~$200–$2,000+ (usage dependent)
- Monitoring/alerting: ~$20–$100

**Estimated total (Full scale self-host): ~$390–$3,100+ / month**

### Notes
- Biggest variable is model/API usage and query volume.
- Full scale may require splitting services or adding queue/caching layers.

---

## Option B — Managed third-party hosting

## B1) MVP (math.AG first)

### Recommended managed stack
- Managed Postgres (Neon/Supabase/RDS)
- Managed vector DB (Qdrant Cloud or pgvector managed)
- Object storage (R2/S3)
- App hosting (Railway/Fly/Render)
- External LLM/embedding API

### MVP monthly cost breakdown (managed)
- Managed Postgres: ~$20–$60
- Managed vector DB: ~$30–$100
- Object storage: ~$5–$30
- App hosting (API + worker): ~$20–$80
- LLM + embeddings API usage: ~$50–$150
- Monitoring/logging: ~$0–$30

**Estimated total (MVP managed): ~$125–$450 / month**

### Notes
- Higher infra subscription vs self-host.
- Much lower operational burden and faster setup.

---

## B2) Full scale (whole arXiv math + higher traffic)

### Recommended managed stack
- Larger managed Postgres tier (+ read replicas as needed)
- Dedicated vector cluster
- Managed search (OpenSearch optional at this stage)
- Dedicated app + worker services
- Queue/cache (optional but likely)
- External LLM/embedding API

### Full-scale monthly cost breakdown (managed)
- Managed Postgres: ~$100–$600
- Managed vector DB: ~$150–$1,000
- Object storage: ~$20–$150
- App/worker hosting: ~$100–$800
- Optional OpenSearch: ~$100–$700
- LLM + embeddings API usage: ~$200–$3,000+
- Monitoring/logging: ~$30–$200

**Estimated total (Full scale managed): ~$700–$6,450+ / month**

### Notes
- Easiest to operate at scale, but expensive.
- Use quotas, caching, and model routing aggressively.

---

## Cost drivers (both options)

1. LLM token usage (answer generation)
2. Embedding volume (index growth)
3. Vector index size and query load
4. Degree of full-text chunking
5. Concurrency and latency targets

---

## Budget control levers

1. Restrict scope by category (start with math.AG)
2. Index abstract + selective passages first
3. Cache repeated queries and evidence packs
4. Use cheaper models for non-final steps
5. Set per-user and global rate limits
6. Set hard monthly budget alerts and throttles

---

## Recommendation by budget band

- **Under $150/mo:** Self-host MVP, strict scope, low traffic expectations.
- **$150–$300/mo:** Managed MVP (best balance), careful model/caching controls.
- **$300–$800/mo:** Strong managed pilot with better reliability and UX.
- **$800+/mo:** Scale-focused architecture and broader corpus depth.

---

## Immediate fit for current plan

Given target cap of **$300/mo**:

- Best fit: **Managed MVP** with strict controls, or self-host + external models.
- Recommended launch scope: **math.AG first**, then expand by measured demand.
