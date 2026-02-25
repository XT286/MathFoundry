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
1. Fill `benchmark/queries.jsonl`
2. Generate results for S0/S1/S2 into `results/`
3. Run `scripts/score.py`
4. Review `results/summary.json`
