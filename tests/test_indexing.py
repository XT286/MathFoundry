from mathfoundry.indexing import _split_passages


def test_split_passages_detects_mathy_blocks():
    summary = "We prove a theorem on schemes. The proof uses cohomology and an example over k."
    passages = _split_passages(summary, "arxiv:test")
    assert len(passages) >= 1
    assert any(p["block_type"] in {"theorem", "proof", "example"} for p in passages)
    assert all(0.0 <= p["math_density"] <= 1.0 for p in passages)
