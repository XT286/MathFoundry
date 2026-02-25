from fastapi import FastAPI

from .config import CONFIG
from .grounding import answer_with_grounding, verify_grounded_answer
from .models import QARequest, SearchRequest, VerifyRequest
from .retrieval import search

app = FastAPI(title="MathFoundry", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "budget_cap_usd": CONFIG.monthly_budget_usd,
        "primary_category": CONFIG.arxiv_primary_category,
        "strict_abstain": CONFIG.strict_abstain,
        "max_raw_files": CONFIG.max_raw_files,
        "max_results_per_ingest": CONFIG.max_results_per_ingest,
        "data_dir": CONFIG.data_dir,
    }


@app.post("/search")
def search_endpoint(req: SearchRequest) -> dict:
    results = search(req)
    return {"query": req.query, "count": len(results), "results": results}


@app.post("/qa")
def qa_endpoint(req: QARequest) -> dict:
    candidates = search(SearchRequest(query=req.query, limit=10))
    grounded = answer_with_grounding(req.query, candidates)
    return grounded.model_dump()


@app.post("/qa/verify")
def qa_verify_endpoint(req: VerifyRequest) -> dict:
    result = verify_grounded_answer(req.answer)
    return result.model_dump()
