# MathFoundry

Open-source, citation-grounded research agent for foundational mathematics literature.

## Positioning
MathFoundry is not just a reference finder and not plain RAG.

- **Vs search-only tools:** MathFoundry answers questions directly, then shows claim-level evidence.
- **Vs generic LLM assistants:** MathFoundry is math-first and enforces “no citation, no claim.”
- **Vs standard RAG:** MathFoundry adds claim-to-citation verification, confidence scoring, and abstention when evidence is insufficient.

## Current docs
- `docs/PRD.md`
- `docs/RFC-INDEX.md`
- `docs/RFC-0001-citation-grounded-qa-architecture.md`
- `docs/RFC-0002-ingestion-and-canonical-schema.md`
- `docs/RFC-0003-retrieval-and-reranking-strategy.md`
- `docs/RFC-0004-grounded-answer-generation-and-citation-verification.md`
- `docs/RFC-0005-hosted-deployment-and-cost-model.md`
- `docs/RFC-0006-web-ux-and-ask-interaction-model.md`
- `docs/SELF-HOST-SETUP.md`

## MVP focus
- arXiv-first ingestion (initial scope: `math.AG`)
- Hybrid retrieval (lexical + semantic)
- Citation-grounded QA (abstain on weak evidence)

## Vertical-slice scaffold (in progress)
- FastAPI endpoints: `/health`, `/search`, `/qa`
- Grounded answer contract skeleton
- arXiv `math.AG` ingestion script (`scripts/ingest_arxiv_math_ag.py`)
- Self-host deployment stack (`deploy/docker-compose.selfhost.yml`)
- Initial API tests

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn mathfoundry.app:app --reload
```

Run tests:
```bash
pytest
```
