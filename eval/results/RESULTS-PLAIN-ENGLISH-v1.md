# MathFoundry Eval Results (Plain English)

This note summarizes the latest evaluation run in plain language.

## What was evaluated

We split the benchmark into two groups so the comparison is fair:

- **In-corpus track**: 24 queries where retrieval coverage was strong.
- **Weak-corpus track**: 6 queries where retrieval coverage was weaker.

Systems compared:

- **S0 (Pure LLM)**: OpenAI model answers directly with no retrieval grounding.
- **S2 (RAG + verify)**: MathFoundry retrieval + OpenAI synthesis + verification endpoint.

## Data snapshot used

- Corpus file: `data/topic/ag_all_math_ag.jsonl`
- Corpus size at run time: **10,080 papers**

## Run outputs generated

- `eval/results/s2_rag_verify_in_corpus_v1.jsonl` (24 rows)
- `eval/results/s0_pure_llm_in_corpus_v1.jsonl` (24 rows)
- `eval/results/s2_rag_verify_weak_corpus_v1.jsonl` (6 rows)
- `eval/results/s0_pure_llm_weak_corpus_v1.jsonl` (6 rows)

## What happened (quick facts)

### In-corpus track (24 queries)

- S2 found retrieval evidence for every query.
- Average search results returned: **8.0**
- Average references attached in final S2 output: **5.0**
- Verification endpoint returned `verify_ok=true` for **24/24**.
- S2 did **not abstain** on any query in this track.

### Weak-corpus track (6 queries)

- S2 still returned evidence for each query, but with lower retrieval counts.
- Average search results returned: **4.167**
- Average references attached in final S2 output: **3.167**
- Verification endpoint returned `verify_ok=true` for **6/6**.
- S2 did **not abstain** on any query in this track.

## Important interpretation notes

- These outputs are **not final quality judgments yet**.
- Current JSONL results are auto-generated and still need human rubric scoring for:
  - correctness,
  - citation adequacy/precision,
  - overclaim risk,
  - abstention quality.
- `verify_ok=true` here mostly confirms schema/citation consistency checks; it does **not** guarantee mathematical correctness by itself.

## Early qualitative pattern from sample inspection

- **S0 (pure LLM)** tends to provide polished textbook-style answers and external references from model memory.
- **S2 (RAG)** tends to stay closer to retrieved corpus evidence and often states when evidence is weak, but may still sound confident.
- Weak-corpus questions (historical/classic references) are where fairness concerns are most significant and where track separation is most important.

## Recommended next step

Run structured human review on both tracks using a shared rubric, then publish:

1. In-corpus comparison table (primary decision signal)
2. Weak-corpus comparison table (coverage stress test)
3. Error analysis with 5 best + 5 worst examples per system
