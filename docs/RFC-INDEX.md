# MathFoundry RFC Index

This index tracks architecture and product RFCs for MathFoundry.

## Status legend
- `Draft` = proposed, open for review
- `Accepted` = approved baseline
- `Superseded` = replaced by newer RFC
- `Deprecated` = no longer recommended

---

## RFC List

## RFC-0001 — Citation-Grounded QA Architecture
- **Status:** Draft
- **File:** `docs/RFC-0001-citation-grounded-qa-architecture.md`
- **Summary:** Defines MVP architecture and the core policy “No citation, no claim.”

## RFC-0002 — Ingestion Pipeline and Canonical Schema (arXiv-first)
- **Status:** Draft
- **File:** `docs/RFC-0002-ingestion-and-canonical-schema.md`
- **Summary:** Defines ingestion stages, canonical data model, provenance, licensing, and idempotent updates.
- **Depends on:** RFC-0001

## RFC-0003 — Retrieval and Reranking Strategy (Math-Aware Hybrid Search)
- **Status:** Draft
- **File:** `docs/RFC-0003-retrieval-and-reranking-strategy.md`
- **Summary:** Defines hybrid retrieval, reranking policy, evaluation metrics, and latency targets.
- **Depends on:** RFC-0001, RFC-0002

## RFC-0004 — Grounded Answer Generation and Claim-to-Citation Verification
- **Status:** Draft
- **File:** `docs/RFC-0004-grounded-answer-generation-and-citation-verification.md`
- **Summary:** Defines structured grounded-answer contract, verifier pass, confidence scoring, and abstention policy.
- **Depends on:** RFC-0001, RFC-0002, RFC-0003

## RFC-0005 — Hosted Deployment and Cost Model (Resource-Constrained MVP)
- **Status:** Draft
- **File:** `docs/RFC-0005-hosted-deployment-and-cost-model.md`
- **Summary:** Defines managed-cloud architecture, storage tiering, cost controls, and MVP operational targets.
- **Depends on:** RFC-0001, RFC-0002, RFC-0003, RFC-0004

## RFC-0006 — Web UX and “Ask MathFoundry” Interaction Model
- **Status:** Draft
- **File:** `docs/RFC-0006-web-ux-and-ask-interaction-model.md`
- **Summary:** Defines web-first adoption UX: Ask flow, answer/evidence presentation, trust signals, and feedback loop.
- **Depends on:** RFC-0001, RFC-0003, RFC-0004, RFC-0005

---

## Suggested acceptance order
1. RFC-0001
2. RFC-0002
3. RFC-0003
4. RFC-0004
5. RFC-0005
6. RFC-0006

---

## Change policy
- Update this index whenever an RFC is added, accepted, superseded, or deprecated.
- Keep file paths stable; if moved, update links immediately.
