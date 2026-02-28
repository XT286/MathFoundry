# MathFoundry PoC Proof v1 (using existing corpus)

## Scope
This PoC intentionally uses the currently indexed corpus (no additional arXiv expansion).

Goal:
1. Prove the end-to-end evaluation pipeline runs.
2. Produce first artifacts for RAG+verify vs pure-LLM comparison.
3. Document current strengths and limits before stronger A/B claims.

## Dataset and query set
- Query file: `eval/benchmark/ag_queries_v1.jsonl`
- Query count: 30 (algebraic geometry focused)

## Run commands used
```bash
# local app
./.venv/bin/uvicorn mathfoundry.app:app --host 127.0.0.1 --port 8010

# generate S2 + S0 template
./.venv/bin/python eval/scripts/run_baseline_compare.py \
  --base-url http://127.0.0.1:8010 \
  --queries eval/benchmark/ag_queries_v1.jsonl

# score summary
./.venv/bin/python eval/scripts/score.py
```

## Artifacts produced
- `eval/results/s2_rag_verify.jsonl`
- `eval/results/s0_pure_llm_template.jsonl`
- `eval/results/summary.json`

## Current PoC results (S2 only)
From `s2_rag_verify.jsonl` (30 queries):
- Search non-empty: 30/30
- `verify_ok=true`: 30/30
- `must_abstain=true`: 0/30
- Avg claims per answer: 1.0
- Avg references per answer: 1.0

From `summary.json`:
- `s2_rag_verify.count = 30`
- `s0_pure_llm.count = 0` (not yet filled)
- `s1_plain_rag.count = 0` (not yet run)

## Interpretation
What works now:
- End-to-end pipeline (retrieve -> answer -> verify -> score files) is operational.
- Structured outputs and evaluation artifacts are reproducible.

What this PoC does **not** prove yet:
- It does **not** yet prove "RAG+verify > pure LLM" because S0 is still template-only.
- Human-scored rubric fields are still null (`correctness`, `citation_precision`, `overclaim`, `abstention_correct`).

## Next step to complete first comparison proof
1. Fill `eval/results/s0_pure_llm_template.jsonl` with pure-LLM answers for the same 30 queries.
2. Human-review both S0 and S2 with the rubric.
3. Re-run `eval/scripts/score.py`.
4. Publish side-by-side table in `docs/POC-PROOF-v1.md` (v1.1).

## Readiness statement
PoC v1 is complete as an **evaluation pipeline proof**.
The **comparative quality proof** is pending baseline answer population + rubric scoring.
