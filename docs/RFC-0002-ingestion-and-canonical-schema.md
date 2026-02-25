# RFC-0002: Ingestion Pipeline and Canonical Schema (arXiv-first)

- **Status:** Draft
- **Author:** Javis
- **Created:** 2026-02-22
- **Target Version:** MVP (v0.1)
- **Related:** `docs/PRD.md`, `docs/RFC-0001-citation-grounded-qa-architecture.md`

---

## 1. Summary

This RFC defines:

1. the arXiv-first ingestion pipeline,
2. the canonical metadata schema for literature indexing,
3. provenance/licensing requirements,
4. idempotent update and deduplication behavior.

Goal: make data ingestion reproducible, legally compliant, and retrieval-ready for grounded QA.

---

## 2. Motivation

Grounded QA quality depends on corpus quality. Current ad-hoc ingestion patterns often fail due to:

- inconsistent identifiers,
- duplicate records across providers,
- weak provenance,
- schema drift,
- non-reproducible updates.

MathFoundry needs a stable data contract before scaling retrieval or generation.

---

## 3. Goals

1. Define one canonical `Work` model for all sources.
2. Support incremental arXiv ingestion with deterministic upserts.
3. Preserve immutable raw source payloads for audit/rebuild.
4. Track per-record licensing/provenance.
5. Produce retrieval-ready passage chunks and citation edges.

## Non-goals (MVP)

- Full bidirectional sync with every provider.
- Perfect author/entity disambiguation.
- Full theorem-level semantic parsing.

---

## 4. Source strategy (MVP)

## Required
- **arXiv**: primary corpus source.

## Optional enrichers
- **Crossref**: DOI metadata augmentation.
- **OpenAlex**: citation/author enrichment.

Rule: arXiv record remains authoritative for arXiv identifiers and core bibliographic fields.

---

## 5. Ingestion architecture

## 5.1 Stages

1. **Fetch**
   - Pull source records in incremental windows.
2. **Raw persist**
   - Store immutable source payload in `raw_records`.
3. **Normalize**
   - Convert to canonical schema.
4. **Resolve/merge**
   - Deduplicate and merge with existing `works`.
5. **Enrich**
   - Add subject tags, optional MSC mapping, citation links.
6. **Chunk**
   - Build retrieval passages from abstract/full text when allowed.
7. **Index publish**
   - Push to lexical/vector/citation indices.

## 5.2 Job model

Each run is tracked by `ingestion_runs` with:

- source,
- start/end time,
- cursor window,
- counts (`fetched`, `normalized`, `upserted`, `failed`),
- checksum summary,
- status.

---

## 6. Canonical schema

## 6.1 Core tables

### `works`
Primary bibliographic entity.

Fields (minimum MVP):
- `id` (internal UUID)
- `canonical_title`
- `abstract`
- `publication_year`
- `first_published_at`
- `updated_at_source`
- `language`
- `source_primary` (`arxiv` for MVP)
- `work_type` (`preprint`, `article`, ...)
- `created_at`, `updated_at`

### `work_identifiers`
One work can have many identifiers.

Fields:
- `work_id`
- `id_type` (`arxiv`, `doi`, `openalex`, `mr`, etc.)
- `id_value`
- `is_primary`
- unique constraint on (`id_type`, `id_value`)

### `authors`
- `id`, `display_name`, optional normalized form.

### `work_authors`
- `work_id`, `author_id`, `position`.

### `subject_tags`
- `id`, `tag_type` (`arxiv_category`, `msc`, `ag_subarea`), `tag_value`, `label`.

### `work_subject_tags`
- `work_id`, `subject_tag_id`, `is_primary`.

### `citation_edges`
- `source_work_id`, `target_work_id`, `edge_source`, `confidence`.

### `passages`
Retrieval chunk unit.

Fields:
- `id`, `work_id`, `section_label`, `chunk_index`, `text`,
- `char_start`, `char_end`,
- `token_count_est`,
- `license_ok_for_indexing`.

### `license_records`
Per-work legal policy snapshot.

Fields:
- `work_id`
- `license_name`
- `license_url`
- `redistribution_allowed` (bool)
- `fulltext_index_allowed` (bool)
- `snippet_display_allowed` (bool)
- `attribution_required` (bool)
- `policy_source`

### `provenance_records`
- `work_id`
- `source_name`
- `source_record_id`
- `source_url`
- `fetched_at`
- `raw_record_checksum`

### `raw_records`
Immutable source payload archive.

Fields:
- `id`
- `source_name`
- `source_record_id`
- `fetched_at`
- `payload_json`
- `payload_checksum`

### `ingestion_runs`
- run metadata and outcomes (Section 5.2).

---

## 7. Identifier resolution and dedup policy

Resolution priority:

1. exact arXiv id match,
2. exact DOI match,
3. exact OpenAlex id match,
4. fallback fuzzy candidate (`title + first_author + year`) with manual review queue.

MVP policy:

- auto-merge only for high-confidence matches,
- send uncertain matches to `merge_review_queue`.

---

## 8. Incremental update behavior

For arXiv updates:

- use source update timestamp/cursor,
- fetch records updated since last successful cursor,
- upsert canonical `works` and related tables idempotently,
- never mutate `raw_records`.

Re-run guarantees:

- repeating same run window should produce no duplicate canonical entities,
- checksums detect source payload changes.

---

## 9. Passage chunking policy (MVP)

Additionally, AG-focused subarea tags are inferred from title+abstract using a lightweight keyword taxonomy (e.g., birational geometry, moduli, derived AG, arithmetic geometry). These tags are stored and used for retrieval boosts.

Chunking defaults:

- target 500–900 tokens equivalent per chunk,
- overlap ~10–15%,
- preserve section headers where available,
- mark theorem/proof-like sections when detectible by heuristic labels (`Theorem`, `Lemma`, `Proof`, `Example`, etc.).

If full text unavailable or disallowed:

- chunk abstract only,
- set passage scope accordingly.

---

## 10. Licensing and compliance requirements

Hard requirements:

1. Every indexed work must have `license_records` entry.
2. Retrieval output must obey snippet/fulltext display permissions.
3. `LICENSE_MATRIX.md` must map source policy to allowed operations.
4. Takedown operation must support hard hide by identifier.

---

## 11. Operational SLOs (MVP)

- Daily incremental ingestion succeeds >= 95% of days.
- Failed run auto-retry up to 3 attempts.
- Ingestion freshness target: <= 24h lag for arXiv updates.
- Schema migration backward compatibility for one minor release.

---

## 12. API/events emitted by ingestion

Emit events per run:
- `ingestion.run.started`
- `ingestion.record.normalized`
- `ingestion.record.failed`
- `ingestion.run.completed`

Metrics:
- normalization failure rate,
- duplicate merge rate,
- license-missing rate,
- chunk production rate.

---

## 13. Acceptance criteria

RFC-0002 is considered implemented for MVP when:

1. arXiv ingestion job runs daily and idempotently,
2. canonical schema tables exist and are populated,
3. dedup logic resolves obvious duplicates without regressions,
4. every indexed work has provenance + license records,
5. passages are generated and queryable for retrieval,
6. replaying last 7 days does not create duplicate works.

---

## 14. Alternatives considered

1. **No raw payload archive**
   - Rejected: poor auditability/reproducibility.

2. **Source-specific schemas only**
   - Rejected: retrieval and QA orchestration complexity explodes.

3. **Aggressive auto-merge for fuzzy matches**
   - Rejected: high risk of incorrect paper conflation.

---

## 15. Rollout plan

1. Implement schema migrations.
2. Ship arXiv fetch + raw persist.
3. Ship normalize + idempotent upsert.
4. Ship passage chunker + index publish.
5. Add enrichment adapters (Crossref/OpenAlex optional).
6. Run backfill + quality audit.

---

## 16. Open questions

1. Should MSC mapping be heuristic-only in MVP or require curated seed mappings?
2. Which citation extraction fallback should be default when references are malformed?
3. Do we need a separate `concept_mentions` table in MVP or phase 2?
4. Should merge review be internal-only initially or exposed to trusted contributors?

---

## Implementation checklist (MVP)

- [ ] Ship schema migrations for all core tables listed in Section 6.
- [ ] Implement `arxiv` ingestion worker with cursor-based incremental sync.
- [ ] Persist immutable raw payloads and checksums before normalization.
- [ ] Implement idempotent upsert + dedup path with deterministic merge rules.
- [ ] Enforce license/provenance record creation as a hard write requirement.
- [ ] Add replay test (`last 7 days`) to CI/staging to validate no duplicate works.

## 17. Decision record

Pending maintainer approval.

Upon acceptance, RFC-0002 becomes the normative ingestion/schema contract for MVP development.
