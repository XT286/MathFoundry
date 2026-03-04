# Human Review Guideline (S0 vs S2)

Use this guide to score outputs consistently across systems and query tracks.

## Goal

Judge answer quality fairly, especially when corpus coverage differs.

- **Primary comparison**: in-corpus track
- **Secondary comparison**: weak-corpus track

Do not mix those two tracks into one single conclusion.

## What to review

For each query, review:

1. `s0_pure_llm_*` row (pure LLM)
2. `s2_rag_verify_*` row (RAG + verify)

Files to review:

- `eval/results/s0_pure_llm_in_corpus_v1.jsonl`
- `eval/results/s2_rag_verify_in_corpus_v1.jsonl`
- `eval/results/s0_pure_llm_weak_corpus_v1.jsonl`
- `eval/results/s2_rag_verify_weak_corpus_v1.jsonl`

## Scoring fields (fill per row)

Set these fields in each reviewed row:

- `correctness` (0.0-1.0)
- `citation_precision` (0.0-1.0)
- `overclaim` (true/false)
- `abstained` (true/false)
- `abstention_correct` (true/false/null)
- `notes` (1-3 lines: why)

## Practical scoring rubric

### 1) Correctness (0.0-1.0)

- **1.0**: mathematically correct, no major errors, fits the question.
- **0.7-0.9**: mostly correct, minor omissions or loose phrasing.
- **0.4-0.6**: mixed quality, partially correct but important issues.
- **0.0-0.3**: wrong, misleading, or irrelevant.

### 2) Citation precision (0.0-1.0)

For S2:
- **1.0**: cited sources clearly support the key claims.
- **0.5**: citations somewhat related but weak support.
- **0.0**: citations do not support the claims.

For S0:
- Keep this near **0.0** unless the model gives verifiable specific references that actually support the claims.

### 3) Overclaim (true/false)

Set `overclaim=true` if the answer:

- states certainty without support,
- claims \"definitive\" resolution where evidence is partial,
- gives fabricated or dubious references as if certain.

### 4) Abstention and abstention correctness

- `abstained=true` if the answer explicitly says evidence is insufficient / cannot conclude.
- `abstention_correct=true` only if abstaining was the right behavior for the query and available evidence.
- If no abstention happened, set `abstention_correct=null`.

## Fairness rules during review

1. Judge S2 by **retrieved evidence quality**, not external memory.
2. Judge S0 by **internal coherence + factual plausibility**, but penalize unsupported certainty.
3. For weak-corpus queries, allow lower completeness for S2 if it is honest about limits.
4. Do not reward hallucinated confidence.

## Suggested workflow

1. Review all in-corpus queries first (primary scorecard).
2. Review weak-corpus queries second (coverage stress test).
3. For each query, compare S0 and S2 side-by-side before final scoring.
4. Mark 3 tags in `notes` when useful:
   - `missing_canonical_ref`
   - `weak_grounding`
   - `good_abstention`

## Recommended acceptance thresholds (team decision aid)

For in-corpus track:

- Mean correctness >= 0.75
- Mean citation precision (S2) >= 0.70
- Overclaim rate <= 0.20

If two systems are close on correctness, prefer the one with:

1. lower overclaim rate
2. better citation precision
3. better abstention correctness

## Output summary template

After review, publish:

- in-corpus: S0 vs S2 table
- weak-corpus: S0 vs S2 table
- top 5 wins and top 5 failures with short notes
