# MathFoundry Evaluation Plan (RAG + Verification vs Baselines)

## Goal
Measure whether MathFoundry's **RAG + verification** improves trust and correctness over:
1. Pure LLM (no retrieval)
2. Plain RAG (retrieval + answer, no verifier)

## Systems compared
- **S0 Pure LLM**
- **S1 Plain RAG**
- **S2 MathFoundry (RAG + verification + abstention)**

## Benchmark design
Use a fixed query set spanning:
- Topology / Geometry / Analysis / Algebra
- Query intents:
  - theorem lookup
  - foundational references
  - compare approaches
  - prerequisites
- Include ambiguous/under-specified prompts to test abstention.

## Metrics
### Retrieval (S1/S2)
- Recall@k
- nDCG@k
- MRR@k

### Answer quality (all)
- Claim correctness (expert reviewed)
- Citation precision (citations support claims)
- Overclaim rate (unsupported confident statements)
- Abstention correctness

### Utility/trust
- Usefulness score (1–5)
- “Would use in real research?” (yes/no)

## Procedure
1. Run all systems on same query set.
2. Store outputs in normalized JSON (`eval/results/*.jsonl`).
3. Run automatic checks for citation structure/resolution.
4. Run human review on sampled outputs.
5. Compare aggregate metrics + error taxonomy.

## Success criteria for S2
S2 should outperform S0 and S1 on:
- lower overclaim rate
- higher citation precision
- better abstention correctness
- higher expert trust score

## Error taxonomy
Tag failures as:
- retrieval miss
- citation mismatch
- unsupported synthesis
- theorem scope error
- abstention failure

Use taxonomy to prioritize fixes (retrieval vs verifier vs prompt/policy).
