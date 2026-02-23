# RFC-0005: Hosted Deployment and Cost Model (Resource-Constrained MVP)

- **Status:** Draft
- **Author:** Javis
- **Created:** 2026-02-22
- **Target Version:** MVP (v0.1)
- **Related:**
  - `docs/PRD.md`
  - `docs/RFC-0001-citation-grounded-qa-architecture.md`
  - `docs/RFC-0002-ingestion-and-canonical-schema.md`
  - `docs/RFC-0003-retrieval-and-reranking-strategy.md`
  - `docs/RFC-0004-grounded-answer-generation-and-citation-verification.md`

---

## 1. Summary

This RFC defines a **hosted-first deployment** for MathFoundry so MVP can run without requiring local storage/infra from Mr. Stark.

Design objective: deliver a usable, citation-grounded math QA agent with minimal operational burden and controlled cost.

---

## 2. Motivation

Local-machine deployment is not viable for MVP due to:

- storage growth of corpus/indexes,
- compute and uptime constraints,
- operational complexity (backups, scaling, monitoring).

A managed-cloud architecture enables fast launch, lower maintenance, and predictable costs.

---

## 3. Goals

1. Run MathFoundry entirely on hosted services.
2. Keep monthly costs bounded in MVP.
3. Avoid provider lock-in where practical.
4. Support daily ingestion and interactive query latency.

## Non-goals (MVP)

- Self-hosted bare metal guidance.
- Multi-region HA architecture.
- Enterprise compliance stack (SOC2/HIPAA equivalents).

---

## 4. Deployment principles

1. **Managed over self-hosted** for DB/search/storage.
2. **Stateless API** services for easy scaling/restarts.
3. **Storage tiering**: raw blobs in object storage, query-critical data in DB/vector index.
4. **Graceful degradation** when expensive components fail (e.g., fallback lexical-only retrieval).
5. **Cost-aware defaults** (math subset scope, passage limits, caching).

---

## 5. Proposed MVP architecture

## 5.1 Core components

1. **API service (FastAPI)**
   - Hosted on Fly.io / Railway / Render (one primary service).
2. **Metadata database (Postgres managed)**
   - Neon / Supabase / AWS RDS.
3. **Vector index (managed)**
   - Qdrant Cloud (preferred) or pgvector on managed Postgres for smallest setup.
4. **Object storage**
   - Cloudflare R2 or S3 for raw payload snapshots and artifacts.
5. **Background jobs**
   - Scheduled worker (same platform cron/worker) for ingestion, chunking, indexing.
6. **Monitoring/logging**
   - Basic hosted logs + metric dashboards (latency/error/ingestion freshness).

## 5.2 Data flow

1. Ingestion worker fetches arXiv deltas.
2. Raw payloads stored in object storage.
3. Canonical records upserted into Postgres.
4. Passages embedded and stored in vector index.
5. API queries retrieval stack and returns grounded answers with citations.

---

## 6. Storage strategy

## 6.1 What we store in each tier

### Object storage (cheap, durable)
- raw source payload snapshots,
- ingestion artifacts,
- optional export files.

### Postgres (query-critical metadata)
- works/authors/subjects/identifiers,
- citation edges,
- provenance and license records,
- ingestion run metadata.

### Vector DB
- passage embeddings + metadata pointers.

## 6.2 Space minimization policies

- Start with **math-only arXiv categories**.
- Store abstract + selected sections/passage windows in MVP.
- Keep full raw payload compressed in object storage only.
- Deduplicate aggressively by identifiers.
- Apply retention/version policy for transient artifacts.

---

## 7. Cost model (rough MVP bands)

> Note: ranges are directional and depend on usage/query volume.

## 7.1 Lean MVP (single maintainer, low traffic)
- API hosting: low tier
- Postgres: starter tier
- Vector DB: starter tier
- Object storage: low volume
- **Estimated monthly:** low double-digit to low triple-digit USD

## 7.2 Active pilot (10–100 frequent users)
- Higher compute + larger vector footprint
- More embeddings and query load
- **Estimated monthly:** mid triple-digit USD range

## 7.3 Cost drivers

1. Embedding volume (new passage indexing)
2. Vector storage size
3. Query traffic (retrieval + generation)
4. LLM inference costs
5. Egress and logs (if unbounded)

---

## 8. Cost-control policies (MVP defaults)

1. **Scope gate**: ingest only arXiv math categories initially.
2. **Chunk budget**: cap passages per work for MVP.
3. **Embedding queue**: async batches, off-peak processing.
4. **Query cache**: cache repeated queries/evidence packs.
5. **Model routing**: cheaper model for retrieval/rerank heuristics, stronger model only for final grounded synthesis.
6. **Rate limits**: per-user/API key query caps.
7. **Observability budget alerts**: monthly spend threshold alerts.

---

## 9. Reliability/SLO targets (MVP)

- API availability: >= 99% (single region target)
- Daily ingestion freshness: <= 24h lag
- P95 query latency: <= 6s for grounded answer path
- Backup policy:
  - daily Postgres snapshot,
  - object storage versioning enabled,
  - weekly restore test in staging (lightweight)

---

## 10. Security baseline

- Secrets in platform secret manager only.
- TLS for all external connections.
- Signed service-to-service credentials where supported.
- Least-privilege DB roles.
- Audit logs for admin-level operations.
- PII minimization (most workloads are literature metadata).

---

## 11. Deployment environments

1. **Dev** (cheap, ephemeral)
2. **Staging** (production-like, reduced data volume)
3. **Prod** (public MVP)

Promotion rule: only deploy to prod after benchmark and grounding checks pass in staging.

---

## 12. Rollout plan

1. Stand up managed Postgres + object storage.
2. Deploy API and worker in one hosted environment.
3. Add vector DB and embedding pipeline.
4. Backfill initial arXiv math subset.
5. Enable web UI and limited external beta.
6. Add budget alerts and usage dashboards.

---

## 13. Acceptance criteria

RFC-0005 is implemented for MVP when:

1. system runs fully hosted with no local-machine dependency,
2. daily ingestion and QA endpoints operate in production,
3. storage tiers are separated (raw/object, metadata/db, vectors/index),
4. budget monitoring is active,
5. observed monthly spend remains within agreed MVP range for pilot usage.

---

## 14. Alternatives considered

1. **Full local deployment**
   - Rejected: insufficient storage/ops capacity.
2. **Single-database-only architecture**
   - Rejected for scaling and retrieval quality constraints.
3. **On-demand fetch only (no local index)**
   - Rejected: poor latency and weak relevance/grounding.

---

## 15. Open questions

1. Should MVP use pgvector-only first to minimize moving parts?
2. Which provider pairing gives best cost/performance (Neon+Qdrant vs Supabase+pgvector)?
3. What monthly budget cap should enforce automatic throttling?
4. Should beta users receive per-user quota controls at launch?

---

## Implementation checklist (MVP)

- [ ] Provision managed Postgres, vector store, and object storage in one cloud region.
- [ ] Deploy stateless API + scheduled worker with secrets manager integration.
- [ ] Configure backups (DB snapshots + object versioning) and restore test procedure.
- [ ] Implement budget alerts and quota/rate-limit defaults.
- [ ] Load-test staging and verify query latency + ingestion freshness SLOs.
- [ ] Document runbooks for outage fallback (lexical-only mode, worker retries).

## 16. Decision record

Pending maintainer approval.

On acceptance, RFC-0005 becomes the deployment and cost baseline for MVP operations.
