# RFC-0001: Citation-Grounded QA Architecture for MathFoundry

- **Status:** Draft
- **Author:** Javis
- **Created:** 2026-02-22
- **Target Version:** MVP (v0.1)
- **Related:** `docs/PRD.md`

---

## 1. Summary

This RFC defines the MVP architecture for MathFoundry: an open-source agent that retrieves and answers mathematics literature queries with strict citation grounding.

Core policy: **No citation, no claim.**

---

## 2. Motivation

Generic LLM assistants fail mathematicians in three common ways:

1. return irrelevant papers,
2. misstate theorem scope/assumptions,
3. produce unsupported claims.

MathFoundry must optimize for **trust and correctness** over fluent but uncertain output.

---

## 3. Goals

1. Provide high-precision literature search over arXiv math corpus (MVP).
2. Return answers with claim-level evidence and source links.
3. Support topology, geometry, analysis, algebra first-class; remain extensible to all branches.
4. Provide explicit abstention when evidence is insufficient.

## Non-goals (MVP)

- Formal proof verification.
- Full theorem formalization.
- Redistribution of restricted full text.

---

## 4. User-facing requirements

For each answer, system must return:

- ranked references,
- concise synthesis,
- inline citations for each substantive claim,
- confidence state: `high | medium | low | insufficient_evidence`.

If grounding fails, system must return:

- `insufficient_evidence`,
- query refinement suggestions,
- closest related references without overclaiming.

---

## 5. Proposed architecture

## 5.1 Ingestion

**Initial sources:** arXiv (required), Crossref/OpenAlex (metadata enrichment optional in MVP).

Pipeline:

1. Fetch new/updated records.
2. Store immutable raw payloads.
3. Normalize into canonical work schema.
4. Parse available text and sections.
5. Attach license/provenance metadata.

## 5.2 Canonical data model (MVP)

Entities:

- `Work` (title, abstract, identifiers, dates)
- `Author`
- `SubjectTag` (arXiv category + optional MSC mapping)
- `Passage` (chunked text with section context)
- `CitationEdge` (work-to-work)
- `LicenseRecord`

Design rule: every generated citation must resolve to a `Work` and optionally `Passage`.

## 5.3 Indexing

Two retrieval indices:

1. **Lexical index** (BM25): robust exact-match behavior for technical phrases.
2. **Vector index** (embeddings): semantic recall for concept-level queries.

Optional graph expansion:

- one-hop citation neighbor expansion for top candidates.

## 5.4 Retrieval orchestration

Request flow:

1. Parse query intent (`lookup | survey | compare | prerequisites`).
2. Retrieve lexical candidates.
3. Retrieve vector candidates.
4. Merge + deduplicate candidates.
5. Rerank using relevance + citation/context features.
6. Build evidence pack (passages + metadata).

## 5.5 Answer generation

Generation runs with constrained input = evidence pack only.

Output contract:

- `answer_summary`
- `claims[]` each with `supporting_citations[]`
- `references[]`
- `confidence`
- `limitations`

Post-check:

- reject claims lacking support,
- downgrade confidence or abstain.

---

## 6. Grounding and safety policy

Hard rules:

1. Do not present uncited mathematical claims as facts.
2. Do not infer theorem statements beyond cited evidence.
3. Prefer abstention over speculative synthesis.
4. Always expose provenance: source id, title, and link.

---

## 7. Evaluation plan (MVP)

## 7.1 Retrieval metrics

- Recall@20
- nDCG@10
- MRR

Measured on curated branch-balanced query set.

## 7.2 Answer quality metrics

- citation precision (claim supported by cited source),
- factual correctness (expert review),
- abstention correctness.

## 7.3 Release gates

MVP must meet minimum thresholds before public release:

- citation precision >= 0.90 on validation set,
- abstention correctness >= 0.80,
- no critical licensing/provenance violations.

(Thresholds can be revised by maintainers via RFC amendment.)

---

## 8. API surface (MVP draft)

- `POST /search`
  - input: query, filters
  - output: ranked works + relevance explanations

- `POST /qa`
  - input: natural language question, optional scope filters
  - output: grounded answer contract (Section 5.5)

- `GET /work/{id}`
  - metadata + citation neighbors + passages

---

## 9. Licensing and compliance

Per-record licensing is mandatory.

MVP policy:

- index and expose only fields permitted by source terms,
- keep `LICENSE_MATRIX.md` and source policy config,
- support takedown/removal workflow.

---

## 10. Operational concerns

- Incremental indexing schedule: daily.
- Full rebuild schedule: weekly (or on schema migrations).
- Observability: request latency, retrieval quality counters, abstention rates, citation failures.
- Reproducibility: version datasets + index snapshots.

---

## 11. Alternatives considered

1. **LLM-only (no retrieval constraints)**
   - Rejected: unacceptable hallucination risk.

2. **Lexical-only retrieval**
   - Rejected: poor semantic recall.

3. **Vector-only retrieval**
   - Rejected: weak exact-match behavior for technical terminology and symbols.

Chosen approach: hybrid retrieval + grounded generation.

---

## 12. Rollout plan

1. Implement ingestion + canonical schema.
2. Ship `/search` with hybrid retrieval.
3. Ship `/qa` with strict citation contract and abstention.
4. Run expert validation set.
5. Publish MVP once release gates pass.

---

## 13. Open questions

1. Should MSC2020 mapping be required in MVP or phase 2?
2. Which embedding model best preserves math semantics for arXiv text?
3. How much section-aware parsing is needed before theorem-level QA is reliable?
4. Should confidence scoring be model-based, rule-based, or hybrid?

---

## Implementation checklist (MVP)

- [ ] Confirm this RFC is accepted before implementing dependent RFCs.
- [ ] Finalize canonical API contracts (`/search`, `/qa`, `/work/{id}`) and publish schemas.
- [ ] Lock release-gate metric definitions and measurement scripts.
- [ ] Create architecture decision log entries for any deviations from this baseline.
- [ ] Open implementation epics that map 1:1 to RFC-0002 through RFC-0006.

## 14. Decision record

Pending maintainer approval.

On acceptance, this RFC becomes the authoritative architecture baseline for MVP implementation.
