from mathfoundry.app import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["primary_category"] == "math.AG"


def test_qa_abstains_when_no_candidates():
    r = client.post("/qa", json={"query": "totally unrelated query zzz"})
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] == "insufficient_evidence"


def test_search_returns_demo_for_ag_terms():
    r = client.post("/search", json={"query": "algebraic geometry cohomology"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1


def test_verify_flags_uncited_claims():
    payload = {
        "answer": {
            "answer_summary": "x",
            "claims": [{"text": "uncited claim", "supporting_citations": []}],
            "references": [],
            "confidence": "low",
            "limitations": [],
            "query_refinements": [],
        }
    }
    r = client.post("/qa/verify", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["invalid_claim_indices"] == [0]
