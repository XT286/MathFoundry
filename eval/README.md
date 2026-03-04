# Eval Folder

This folder contains benchmark inputs, run outputs, and scoring scripts for comparing:
- pure LLM
- plain RAG
- MathFoundry (RAG + verification)

## Layout
- `benchmark/queries.jsonl` : canonical query set
- `results/` : model outputs by system and run
- `rubric/reviewer-form.md` : human evaluation rubric
- `scripts/` : evaluation tooling

## Quick flow
1. Fill `benchmark/queries.jsonl` (or use `benchmark/ag_queries_v1.jsonl`)
2. Generate results for S0/S1/S2 into `results/`
3. Run `scripts/score.py`
4. Review `results/summary.json`

## Fair Comparison Policy (RAG vs Pure LLM)

To keep comparison fair when corpus coverage is incomplete:

1. Split benchmark queries into two tracks:
   - **In-corpus track**: retrieval has strong support (recommended threshold: `max_score >= 0.75`)
   - **Weak-corpus track**: retrieval is weak or sparse (`max_score < 0.75`)
2. Report all metrics separately for both tracks.
3. For RAG, low-retrieval-confidence queries should abstain or propose query refinements.
4. Do not use weak-corpus queries alone to conclude pure LLM superiority; they measure pretrained prior knowledge more than retrieval quality.

Suggested split files:
- `benchmark/ag_queries_in_corpus_v1.jsonl`
- `benchmark/ag_queries_weak_corpus_v1.jsonl`

## Recommended RAG Metrics

### Retrieval metrics
- `Recall@k` / `Hit@k`
- `MRR@k`
- `nDCG@k`
- `Precision@k`

### Grounding / faithfulness metrics
- Citation precision (claims supported by cited references)
- Citation recall (important claims cited)
- Hallucination rate / unsupported claim rate
- Verification pass rate (`verify_ok`, coverage ratio)

### Answer quality metrics
- Correctness (human or LLM-judge rubric)
- Completeness/helpfulness
- Abstention quality (abstain precision/recall)

### System metrics
- Latency (p50/p95)
- Token usage
- Cost per query
- Failure/timeout rate

## OpenAI-based runs (latest ChatGPT API model)
Set API key:

```bash
export OPENAI_API_KEY=... 
```

Pure LLM baseline (S0):

```bash
python eval/scripts/run_s0_openai.py \
  --model gpt-4.1 \
  --queries eval/benchmark/ag_queries_v1.jsonl \
  --out eval/results/s0_pure_llm.jsonl
```

RAG + verify with OpenAI generation (S2):

```bash
python eval/scripts/run_s2_openai_rag.py \
  --model gpt-4.1 \
  --base-url http://127.0.0.1:8000 \
  --queries eval/benchmark/ag_queries_v1.jsonl \
  --out eval/results/s2_rag_verify.jsonl
```

Score:

```bash
python eval/scripts/score.py
```

## Current Evaluation Plan

1. Freeze corpus/index snapshot for reproducibility.
2. Build in-corpus vs weak-corpus query splits from retrieval coverage.
3. Run S0 and S2 on **in-corpus** track first (primary fairness comparison).
4. Run S0 and S2 on weak-corpus track (stress/coverage analysis).
5. Score and publish side-by-side summary for both tracks.
