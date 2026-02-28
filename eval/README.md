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
