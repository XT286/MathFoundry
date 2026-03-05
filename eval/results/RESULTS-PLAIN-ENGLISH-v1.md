# MathFoundry Eval Results (Plain English, Updated)

This note summarizes the **current** run outputs and includes explicit **S0 vs S2 comparison**.

## Scope

Benchmark was split for fairness:

- **In-corpus track**: 24 queries (strong retrieval coverage)
- **Weak-corpus track**: 6 queries (weaker retrieval coverage)

Systems:

- **S0 (Pure LLM)**: model answers directly, no retrieval grounding
- **S2 (RAG + verify)**: retrieval + OpenAI synthesis + `/qa/verify` checks

Model used for this latest run:

- **`gpt-5.3-chat-latest`**

Data snapshot:

- Corpus file: `data/topic/ag_all_math_ag.jsonl`
- Corpus size at run: **10,080 papers**

Output files (latest GPT-5.x run):

- `eval/results/s0_pure_llm_in_corpus_gpt53_v1.jsonl` (24)
- `eval/results/s2_rag_verify_in_corpus_gpt53_v1.jsonl` (24)
- `eval/results/s0_pure_llm_weak_corpus_gpt53_v1.jsonl` (6)
- `eval/results/s2_rag_verify_weak_corpus_gpt53_v1.jsonl` (6)

## Side-by-side comparison

### In-corpus track (24 queries)

- **Coverage**:
  - S2: avg `search_count` = **8.0**, avg `references` = **5.0**
  - S0: no retrieval/citation grounding fields
- **Verification**:
  - S2 `verify_ok`: **24/24 (100%)**
  - S2 `must_abstain`: **0/24**
- **Answer length profile** (character count):
  - S0 mean: **2351.0**
  - S2 mean: **1160.8**
  - S0 answers are roughly **2x longer** on average.

Interpretation: in in-corpus cases, S2 is more concise and evidence-attached; S0 is more expansive but not retrieval-grounded.

### Weak-corpus track (6 queries)

- **Coverage**:
  - S2 avg `search_count` = **4.167**
  - S2 avg `references` = **3.167**
- **Verification**:
  - S2 `verify_ok`: **6/6 (100%)**
  - S2 `must_abstain`: **0/6**
- **Answer length profile**:
  - S0 mean: **2136.5**
  - S2 mean: **931.7**
  - S0 is roughly **2.3x longer** on average.

Interpretation: in weak-corpus cases, S2 still produces grounded outputs but with thinner retrieval support; S0 remains long and fluent, likely drawing more from model prior knowledge.

## Notable behavior differences

- S0 tends to give textbook-style, broad answers with external-looking references and higher verbosity.
- S2 tends to stay within retrieved paper context and produces shorter, tighter summaries.
- Largest S0-vs-S2 gaps still appear on classic/historical questions, where retrieval support is weakest.

## What these results do *not* prove yet

These files are still **pre-rubric**. They do not yet provide final judgments on:

- mathematical correctness,
- citation adequacy quality,
- overclaim risk,
- abstention quality.

Also, `verify_ok=true` indicates structural/citation consistency checks passed, not guaranteed mathematical truth.

## Next step (to finalize comparison)

Use `eval/rubric/review_sheet_v1.csv` + `eval/rubric/HUMAN-REVIEW-GUIDELINE-v1.md` to complete human scoring, then publish final S0 vs S2 scorecards:

1. In-corpus (primary decision metric)
2. Weak-corpus (stress/coverage diagnostic)
