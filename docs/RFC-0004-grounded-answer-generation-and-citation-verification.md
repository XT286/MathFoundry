# RFC-0004: Grounded Answer Generation and Claim-to-Citation Verification

- **Status:** Draft
- **Author:** Javis
- **Created:** 2026-02-22
- **Target Version:** MVP (v0.1)
- **Related:**
  - `docs/PRD.md`
  - `docs/RFC-0001-citation-grounded-qa-architecture.md`
  - `docs/RFC-0002-ingestion-and-canonical-schema.md`
  - `docs/RFC-0003-retrieval-and-reranking-strategy.md`

---

## 1. Summary

This RFC defines the answer generation contract for MathFoundry:

1. answers must be grounded only in retrieved evidence,
2. each substantive claim must map to citations,
3. unsupported claims are rejected or downgraded,
4. abstention is first-class behavior.

Core policy: **No citation, no claim.**

---

## 2. Motivation

In math research workflows, users need trustworthy synthesis, not fluent speculation.

Failure modes in generic assistants:

- claims not backed by sources,
- theorem misstatements,
- incorrect scope/assumption transfer,
- fake or irrelevant citations.

This RFC establishes deterministic guardrails for grounded QA.

---

## 3. Goals

1. Produce citation-backed answers for math literature queries.
2. Enforce claim-level support checks.
3. Surface confidence and limitations explicitly.
4. Minimize hallucination risk through abstention and verification.

## Non-goals (MVP)

- Formal proof validation.
- Automatic theorem formalization.
- Guarantee of mathematical truth beyond cited evidence.

---

## 4. Inputs and outputs

## 4.1 Inputs

From retrieval layer (RFC-0003):

- `query`
- `intent`
- `evidence_pack` containing passages, work metadata, citation links, and scores.

## 4.2 Output contract

`GroundedAnswer` object:

- `answer_summary` (concise synthesis)
- `claims[]`
  - `text`
  - `supporting_citations[]` (work_id + optional passage_id)
  - `support_level` (`direct | indirect`)
- `references[]` (deduplicated bibliography)
- `confidence` (`high | medium | low | insufficient_evidence`)
- `limitations[]`
- `query_refinements[]` (when needed)

All user-facing answer formats (web, API, CLI) must preserve this structure.

---

## 5. Generation pipeline

## 5.1 Step A — Draft generation (constrained)

- Model receives only the evidence pack and strict system instructions.
- Model is instructed to avoid uncited claims.
- Model emits structured draft with claim-level citations.

## 5.2 Step B — Verification pass

Automated validator checks each claim:

1. At least one citation exists.
2. Citation resolves to known work (and passage if supplied).
3. Claimed relation is not contradicted by cited passage (heuristic check).

Failures trigger:

- claim removal,
- confidence downgrade,
- or full abstention if answer integrity falls below threshold.

## 5.3 Step C — Policy enforcement

- If verified claim coverage is too low, return `insufficient_evidence`.
- Always include limitations and refinement suggestions when abstaining.

---

## 6. Verification policy

## 6.1 Claim classes

- `factual_lit_claim`: paper/topic attribution
- `comparative_claim`: contrasts between approaches
- `scope_claim`: assumptions, applicability, limitations
- `historical_claim`: chronology, foundational precedence

Higher-risk claim classes (`scope_claim`, `comparative_claim`) require stronger support.

## 6.2 Minimum support requirements

- `factual_lit_claim`: >= 1 direct citation
- `historical_claim`: >= 1 direct citation
- `comparative_claim`: >= 2 citations (or 1 citation + explicit uncertainty)
- `scope_claim`: citation to source text describing assumptions/limits

## 6.3 Citation hygiene

- No dangling citations.
- No duplicate fake IDs.
- No citing works outside retrieved evidence pack (MVP strict mode).

---

## 7. Confidence scoring

Confidence is computed from:

- claim verification pass rate,
- evidence quality (retrieval scores + passage specificity),
- contradiction signals,
- claim type risk profile.

Suggested thresholds (initial):

- `high`: >= 90% verified claims, no high-risk unresolved issues
- `medium`: >= 75% verified claims, minor caveats
- `low`: >= 50% verified claims or significant caveats
- `insufficient_evidence`: < 50% verified or high contradiction/coverage gaps

(Thresholds tuned via evaluation loop.)

---

## 8. Abstention behavior

When abstaining, system must provide:

1. short reason for abstention,
2. top relevant references found,
3. concrete query refinement suggestions,
4. optional filter suggestions (subfield/date/author).

Abstention is success when evidence is weak; it is not treated as a model failure.

---

## 9. Prompting and model constraints

MVP guidance:

- strict JSON schema output from generation layer,
- deterministic-ish decoding for reproducibility,
- no external tool calls inside generation step,
- avoid chain-of-thought disclosure in user output.

System prompts must encode:

- no-citation-no-claim policy,
- citation formatting rules,
- abstention rules,
- limitation disclosure requirement.

---

## 10. Evaluation and QA

## 10.1 Automated checks

- claim coverage (% claims with valid citations)
- citation resolution success
- hallucination proxy rate (uncited/unsupported claims)
- abstention trigger correctness

## 10.2 Human review loop

Math experts score:

- correctness,
- citation adequacy,
- usefulness,
- overclaiming risk.

Feedback feeds:

- prompt/policy tuning,
- verifier heuristics,
- retrieval improvements.

---

## 11. Observability and debugging

Log (with privacy-safe controls):

- query id/intents,
- evidence set size,
- claim counts by type,
- verification failure reasons,
- confidence outcome,
- abstention reason code.

Provide developer tooling:

- answer trace viewer (claim -> citation -> passage),
- failed-claim inspector.

---

## 12. API design (MVP)

### `POST /qa`

Input:
- query
- optional filters
- optional output mode (`brief | detailed`)

Output:
- `GroundedAnswer` contract

### `POST /qa/verify` (internal/admin)

Input:
- candidate grounded answer + evidence pack

Output:
- verification report + pass/fail + reason codes.

---

## 13. Acceptance criteria

RFC-0004 is implemented for MVP when:

1. every substantive claim includes valid citation references,
2. verifier blocks/downgrades unsupported claims,
3. abstention path is available and tested,
4. confidence labels are emitted for all answers,
5. evaluation dashboard tracks claim-grounding metrics,
6. expert review shows meaningful reduction in overclaiming vs baseline.

---

## 14. Alternatives considered

1. **Single-pass generation without verification**
   - Rejected: high hallucination risk.

2. **Reference list only (no claim-level mapping)**
   - Rejected: weak trust and poor auditability.

3. **Always answer, never abstain**
   - Rejected: unacceptable reliability for math use cases.

Chosen: structured generation + explicit verification + abstention.

---

## 15. Open questions

1. Should verifier remain heuristic in MVP or include lightweight NLI checks?
2. What fraction of indirect support is acceptable for comparative claims?
3. Should confidence be calibrated per branch (e.g., algebra vs geometry)?
4. How should multi-paper synthesis uncertainty be communicated in UI?

---

## 16. Decision record

Pending maintainer approval.

On acceptance, RFC-0004 becomes the normative grounded answer/verification contract for MVP.
