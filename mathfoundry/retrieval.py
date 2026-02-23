from .models import SearchRequest


# Placeholder retrieval layer for vertical slice.
# Next step: wire OpenSearch + vector index + citation expansion.
def search(req: SearchRequest) -> list[dict]:
    q = req.query.lower()
    if "algebraic geometry" in q or "scheme" in q or "cohomology" in q:
        return [
            {
                "work_id": "arxiv:math.AG-demo-001",
                "title": "Foundational Topics in Algebraic Geometry (demo)",
                "score": 0.91,
                "source": "arxiv",
            }
        ]
    return []
