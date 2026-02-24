# MathFoundry System Requirements and Cost Options

Last updated: 2026-02-22

This document lists deployment options from **lowest cost to highest cost** and provides requirements + rough cost ranges for:
- **MVP** (algebraic geometry first, low-to-moderate usage)
- **Full scale** (whole arXiv math focus, higher usage)

---

## Assumptions

- Primary use case: citation-grounded QA over arXiv math papers.
- LLM inference starts with external API for quality/stability.
- Costs are rough order-of-magnitude estimates, not quotes.

---

## Option 1 (Lowest Cost) — Fully Self-Hosted

Everything runs on your own server(s): API, worker, Postgres, vector index, and file storage.

## 1.1 MVP (math.AG first)

### Recommended server requirements
- CPU: 8 vCPU
- RAM: 32 GB
- Disk: 1 TB NVMe SSD
- Network: stable broadband, low packet loss
- OS: Ubuntu 22.04+ (or equivalent Linux)

### Services on server
- API service (FastAPI)
- Worker (ingestion/indexing)
- Postgres (+ pgvector)
- Local file storage for raw payloads and artifacts
- Basic local monitoring/logging

### MVP monthly cost breakdown (fully self-hosted)
- Server/VPS: ~$40–$150
- Domain/TLS/misc: ~$0–$10
- Optional offsite backup (cheap cold storage): ~$0–$20
- LLM + embeddings API usage: ~$50–$150

**Estimated total (MVP fully self-hosted): ~$90–$330 / month**

### Notes
- Lowest recurring infra cost.
- Highest operations responsibility (patching, backups, recovery, uptime).

---

## 1.2 Full scale (whole arXiv math + higher traffic)

### Recommended server requirements
- CPU: 16–32 vCPU
- RAM: 64–128 GB
- Disk: 2–4 TB NVMe SSD
- Optional: second node for redundancy/workload split

### Full-scale monthly cost breakdown (fully self-hosted)
- Primary server: ~$150–$500
- Optional secondary node: +$100–$400
- Optional offsite backups: ~$20–$100
- LLM + embeddings API usage: ~$200–$2,000+ (usage dependent)
- Monitoring/alerting (basic-to-moderate): ~$0–$80

**Estimated total (Full scale fully self-hosted): ~$350–$3,080+ / month**

---

## Option 2 (Mid Cost) — Hybrid Self-Hosted + Managed Components

Core services run on your server, but one or two reliability-critical pieces are managed (usually object backup and/or vector DB).

## 2.1 MVP (math.AG first)

### Typical stack
- Self-hosted API + worker + Postgres
- Managed vector DB **or** managed object backup
- External LLM/embedding API

### MVP monthly cost breakdown (hybrid)
- Server/VPS: ~$40–$150
- Managed component(s): ~$20–$120
- Domain/TLS/misc: ~$0–$10
- LLM + embeddings API usage: ~$50–$150
- Monitoring/logging: ~$0–$30

**Estimated total (MVP hybrid): ~$110–$460 / month**

### Notes
- Good compromise between cost and ops burden.
- Easier durability than fully self-hosted.

---

## 2.2 Full scale (whole arXiv math + higher traffic)

### Typical stack
- Self-hosted app + worker tier
- Managed vector and/or managed backup/storage
- Optional managed read replica/search component
- External LLM/embedding API

### Full-scale monthly cost breakdown (hybrid)
- Server(s): ~$150–$800
- Managed components: ~$100–$1,200
- Backups/storage: ~$20–$150
- LLM + embeddings API usage: ~$200–$3,000+
- Monitoring/alerting: ~$20–$120

**Estimated total (Full scale hybrid): ~$490–$5,270+ / month**

---

## Option 3 (Highest Cost) — Fully Managed Third-Party Hosting

Managed Postgres, managed vector DB, managed object storage, managed app hosting, managed observability.

## 3.1 MVP (math.AG first)

### Recommended managed stack
- Managed Postgres (Neon/Supabase/RDS)
- Managed vector DB (Qdrant Cloud or pgvector managed)
- Object storage (R2/S3)
- App hosting (Railway/Fly/Render)
- External LLM/embedding API

### MVP monthly cost breakdown (fully managed)
- Managed Postgres: ~$20–$60
- Managed vector DB: ~$30–$100
- Object storage: ~$5–$30
- App hosting (API + worker): ~$20–$80
- LLM + embeddings API usage: ~$50–$150
- Monitoring/logging: ~$0–$30

**Estimated total (MVP fully managed): ~$125–$450 / month**

---

## 3.2 Full scale (whole arXiv math + higher traffic)

### Recommended managed stack
- Larger managed Postgres tier (+ replicas)
- Dedicated vector cluster
- Managed search (optional but likely)
- Dedicated app + worker services
- Queue/cache
- External LLM/embedding API

### Full-scale monthly cost breakdown (fully managed)
- Managed Postgres: ~$100–$600
- Managed vector DB: ~$150–$1,000
- Object storage: ~$20–$150
- App/worker hosting: ~$100–$800
- Optional OpenSearch: ~$100–$700
- LLM + embeddings API usage: ~$200–$3,000+
- Monitoring/logging: ~$30–$200

**Estimated total (Full scale fully managed): ~$700–$6,450+ / month**

---

## Cost drivers (all options)

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

- **Under $150/mo:** Option 1 (fully self-hosted), strict scope and traffic.
- **$150–$300/mo:** Option 1 or lean Option 2; careful model/caching controls.
- **$300–$800/mo:** Option 2 or lean Option 3 for easier operations.
- **$800+/mo:** Option 3 for scale and team velocity.

---

## Immediate fit for current plan

Given target cap of **$300/mo**:
- Best fit: **Option 1 (fully self-hosted)** or a very lean **Option 2 (hybrid)**.
- Recommended launch scope: **math.AG first**, then expand by measured demand.

---

## Recommended rollout strategy (MVP -> scale)

### Phase 0 — Private MVP / PoC (now)

**Architecture:** Option 1 (fully self-hosted, one rented server)

**Scope:** arXiv `math.AG` only

**Goals:**
- End-to-end flow works: Ask -> grounded answer -> citations/evidence
- Strict abstention when evidence is weak
- 20-50 benchmark queries for internal evaluation
- Basic latency/cost logging

**Gate to move to Phase 1:**
- citation-grounding quality is consistently better than generic baseline,
- system runs stably for at least 2 weeks,
- monthly spend remains under cap.

### Phase 1 — Private beta (small invited users)

**Architecture:** Option 2 (hybrid self-hosted + selected managed components)

**Scope:** Gradual expansion beyond `math.AG` based on demand

**Goals:**
- Improve durability (backups + restore checks)
- Improve operability (monitoring, alerts, rate limits)
- Collect structured user feedback from real mathematicians

**Trigger to move to Phase 2:**
- persistent latency/availability pressure,
- storage/index growth beyond comfortable self-host limits,
- recurring ops burden,
- consistent active usage growth.

### Phase 2 — Public beta / open-source launch

**Architecture:** Option 3 (managed-heavy) or split-service architecture

**Scope:** Wider arXiv math coverage and broader user access

**Goals:**
- Higher reliability and maintainability at scale
- Contributor-friendly workflows (docs/CI/staging)
- Public-facing support and incident handling

### Guiding principle

Start lean and inexpensive, prove trust/value first, and scale infrastructure only when usage and quality metrics justify the additional spend.
