# MathFoundry

Open-source, citation-grounded research agent for foundational mathematics literature.

## Positioning
MathFoundry is not just a reference finder and not plain RAG.

- **Vs search-only tools:** MathFoundry answers questions directly, then shows claim-level evidence.
- **Vs generic LLM assistants:** MathFoundry is math-first and enforces “no citation, no claim.”
- **Vs standard RAG:** MathFoundry adds claim-to-citation verification, confidence scoring, and abstention when evidence is insufficient.

## Current docs
- `docs/PRD.md`
- `docs/RFC-0001-citation-grounded-qa-architecture.md`

## MVP focus
- arXiv-first ingestion
- Hybrid retrieval (lexical + semantic)
- Citation-grounded QA (abstain on weak evidence)
