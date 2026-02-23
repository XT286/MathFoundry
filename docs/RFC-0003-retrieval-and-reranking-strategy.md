# RFC-0003: Retrieval and Reranking Strategy (Math-Aware Hybrid Search)

- **Status:** Draft
- **Author:** Javis
- **Created:** 2026-02-22
- **Target Version:** MVP (v0.1)
- **Related:**
  - `docs/PRD.md`
  - `docs/RFC-0001-citation-grounded-qa-architecture.md`
  - `docs/RFC-0002-ingestion-and-canonical-schema.md`

---

## 1. Summary

This RFC defines the retrieval and reranking stack for MathFoundry MVP.

Decision: use **hybrid retrieval** (lexical + vector + optional citation expansion), followed by a reranking stage optimized for mathematical relevance and grounding quality.

Primary objective: maximize **relevant evidence recall** while preserving precision for theorem-level and concept-level math queries.

---

## 2. Motivation

Math queries fail in generic systems due to:

- notation-sensitive terminology mismatch,
- weak handling of exact phrases and theorem names,
- semantic drift in embedding-only retrieval,
- no use of citation structure.

A hybrid pipeline gives robust exact matching plus conceptual recall, then reranking imposes domain-aware ordering.

---

## 3. Goals

1. Support math-focused queries across topology, geometry, analysis, algebra (extensible to all branches).
2. Return high-quality candidate evidence for grounded QA.
3. Balance exact phrase reliability with semantic discovery.
4. Keep latency acceptable for interactive research workflows.

## Non-goals (MVP)

- End-to-end theorem proving.
- Deep symbolic normalization for all formulas.
- Personalized ranking profiles.

---

## 4. Query classes (MVP)

Retrieval must handle at least:

1. **Lookup**: “paper/theorem X by Y”
2. **Survey**: “foundational references for topic T”
3. **Compare**: “approach A vs B for problem P”
4. **Prerequisite map**: “what to read before paper X”
5. **Related work**: “papers similar to X”

Intent classification is lightweight and rule/model hybrid; fallback is generic hybrid retrieval.

---

## 5. Proposed architecture

## 5.1 Stage A — Query normalization

- Normalize whitespace/case.
- Preserve critical symbols/tokens where possible.
- Expand math-aware aliases and spelling variants (e.g., C*-algebra forms).
- Detect likely theorem/object names for exact boosting.

Output: normalized query object with optional intent, constraints, and expansion terms.

## 5.2 Stage B — Candidate generation

Run in parallel:

1. **Lexical retrieval** (BM25 / OpenSearch)
   - fields: title, abstract, passage text, subject tags.
2. **Vector retrieval** (embedding index)
   - fields: abstract + passages.
3. **Optional citation expansion**
   - one-hop neighbors from top lexical/vector seeds.

Merge candidates via reciprocal rank fusion (RRF) or weighted merge.

## 5.3 Stage C — Candidate filtering

- Deduplicate by `work_id` and passage overlap.
- Apply scope filters (date, subject tags, source).
- Enforce licensing visibility constraints.

## 5.4 Stage D — Reranking

Rerank top-N candidates using a math-aware scoring function:

`final_score = w1*lexical + w2*semantic + w3*citation + w4*field_match + w5*freshness + w6*authority`

Where:
- `lexical`: BM25 score
- `semantic`: embedding similarity
- `citation`: graph centrality/neighbor relevance
- `field_match`: subject tag overlap (arXiv + optional MSC)
- `freshness`: recency (query-dependent)
- `authority`: venue/citation robustness proxy (careful weighting)

Default MVP behavior: avoid over-penalizing older foundational works.

## 5.5 Stage E — Evidence packing for QA

Select top passages across top works with diversity constraints:

- max passages/work,
- min unique works,
- include at least one high-confidence exact-match source if available.

Return structured evidence pack for generation stage.

---

## 6. Ranking policy details

## 6.1 Foundational bias control

For foundational-math intents, reduce recency weight and increase citation/authority weight to avoid ranking only recent papers.

## 6.2 Precision safeguards

- Exact theorem-name matches get controlled boosts.
- If query asks for “foundational/classic,” prefer survey/canonical works.
- If confidence in top set is low, pass uncertainty signal to QA layer.

## 6.3 Diversity constraints

To avoid monoculture output:

- cap repeated authors/venues in top-k,
- include cross-subfield candidates when query is broad.

---

## 7. Data dependencies

Required from RFC-0002 tables:

- `works`, `work_identifiers`, `subject_tags`, `work_subject_tags`, `passages`, `citation_edges`, `license_records`.

Retrieval service must fail closed on missing license permissions for display snippets.

---

## 8. Evaluation plan

## 8.1 Offline retrieval benchmarks

Per branch query sets (topology/geometry/analysis/algebra), target minimum 100 curated queries each over time.

Metrics:

- Recall@20
- nDCG@10
- MRR@10
- branch coverage@k

## 8.2 Online quality metrics

- click-through on top references,
- user save/export actions,
- query reformulation rate,
- “not relevant” feedback rate.

## 8.3 Reranker ablations

Compare:

1. lexical only,
2. vector only,
3. hybrid w/o citation,
4. hybrid + citation,
5. hybrid + citation + field-aware reranker (target).

---

## 9. Performance and SLO targets (MVP)

- P50 retrieval latency <= 1.5s
- P95 retrieval latency <= 4.0s
- index refresh availability >= 99%
- reranker timeout fallback to merged candidate ranking (graceful degradation)

---

## 10. Failure modes and mitigations

1. **Embedding drift / semantic mismatch**
   - Mitigation: maintain lexical channel as hard anchor.

2. **Overfitting to citation popularity**
   - Mitigation: cap authority weight, enforce diversity.

3. **Notation-heavy query miss**
   - Mitigation: theorem/object exact-boost rules + synonym lexicon.

4. **Latency spikes**
   - Mitigation: bounded candidate pools, async graph expansion, reranker timeout fallback.

5. **Cross-branch blind spots**
   - Mitigation: branch-balanced benchmark and coverage audits.

---

## 11. API contract (retrieval service)

### `POST /retrieve`

Input:
- `query`
- optional filters (`date_range`, `subjects`, `sources`)
- optional mode (`lookup|survey|compare|prereq|related`)

Output:
- `candidates[]` with scores by channel,
- `reranked[]` final order,
- `evidence_pack` references for QA,
- `diagnostics` (latency, channel hit counts, confidence).

---

## 12. Rollout plan

1. Implement lexical + vector baseline.
2. Add weighted merge / RRF.
3. Add citation expansion (1-hop).
4. Implement reranker scoring policy.
5. Add branch-balanced benchmark suite.
6. Tune weights and publish default ranking profile.

---

## 13. Acceptance criteria

RFC-0003 is considered implemented for MVP when:

1. hybrid retrieval is default and productionized,
2. reranker outputs deterministic top-k with explainable component scores,
3. branch benchmark metrics beat lexical-only baseline by agreed margins,
4. retrieval outputs stable evidence packs for grounded QA,
5. latency SLOs are met in staging load tests.

---

## 14. Alternatives considered

1. **Lexical-only**
   - Rejected: weak conceptual recall.
2. **Vector-only**
   - Rejected: poor exact match/theorem-name behavior.
3. **LLM rerank-only without explicit features**
   - Rejected for MVP: low transparency and harder debugging.

Chosen: transparent hybrid scoring with optional learned rerank upgrades later.

---

## 15. Open questions

1. Should RRF be default merge or weighted normalized-score merge?
2. Which embedding model best preserves advanced math semantics in MVP constraints?
3. How should we represent symbolic math tokens to improve both lexical and vector channels?
4. Should branch-specific rank profiles be introduced in MVP or phase 2?

---

## Implementation checklist (MVP)

- [ ] Implement lexical and vector retrieval channels with shared query-normalization input.
- [ ] Implement candidate merge (RRF or weighted merge) and lock default in config.
- [ ] Implement reranker with transparent component scores.
- [ ] Add citation one-hop expansion with timeout-safe fallback.
- [ ] Add offline benchmark runner and store baseline vs hybrid comparison outputs.
- [ ] Add latency/perf dashboards and alerting for SLO breaches.

## 16. Decision record

Pending maintainer approval.

On acceptance, RFC-0003 becomes the normative retrieval/reranking contract for MVP.
