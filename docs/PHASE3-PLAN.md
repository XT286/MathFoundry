# Phase 3 Plan (3A + 3B)

## 3A — Evaluation Proof Track
Goal: produce evidence that MathFoundry (RAG + verification) outperforms pure LLM baseline on groundedness.

Steps:
1. Use benchmark query set (`eval/benchmark/queries.jsonl` and AG presets).
2. Generate S2 outputs with verification metadata.
3. Fill S0 (pure LLM) answers using same queries.
4. Score with rubric fields:
   - correctness
   - citation_precision
   - overclaim
   - abstention_correct
5. Run `eval/scripts/score.py` and export summary artifact.

Primary output:
- `eval/results/summary.json`
- side-by-side JSONL files for S0/S2.

## 3B — Focused Corpus Expansion Track
Goal: expand AG corpus safely (paced, checkpointed, storage-aware).

Script:
- `scripts/fetch_ag_focus_10k.py`

Controls (env):
- `MATHFOUNDRY_FOCUS_TARGET`
- `MATHFOUNDRY_FOCUS_PAGE_SIZE`
- `MATHFOUNDRY_FOCUS_MAX_PAGES`
- `MATHFOUNDRY_FOCUS_SLEEP_SEC`
- `MATHFOUNDRY_FOCUS_CHECKPOINT_EVERY`
- `MATHFOUNDRY_STORAGE_BUDGET_GB`
- `MATHFOUNDRY_FOCUS_STOP_RATIO`

Outputs:
- `data/topic/ag_focus_*.jsonl`
- checkpoint JSON in `data/topic/`

Safety:
- Stop if `data/` usage crosses configured storage guard threshold.
