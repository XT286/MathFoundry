from __future__ import annotations

import re
import sqlite3

from .indexing import db_path
from .models import SearchRequest


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9*\-]+", text.lower()) if len(t) >= 2]


def _score(text: str, tokens: list[str]) -> float:
    hay = text.lower()
    if not tokens:
        return 0.0
    hits = 0
    for t in tokens:
        if t in hay:
            hits += 1
    return hits / len(tokens)


def _search_sqlite(req: SearchRequest) -> list[dict]:
    path = db_path()
    if not path.exists():
        return []

    tokens = _tokenize(req.query)
    if not tokens:
        return []

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT p.work_id, p.title, p.summary, p.category, p.published, p.updated,
               ps.text AS passage_text, ps.block_type, ps.math_density
        FROM papers p
        LEFT JOIN passages ps ON ps.work_id = p.work_id
        ORDER BY p.updated DESC
        LIMIT 3000
        """
    ).fetchall()
    conn.close()

    best_by_work: dict[str, dict] = {}
    for r in rows:
        work_id = r["work_id"]
        title = r["title"] or ""
        summary = r["summary"] or ""
        ptext = r["passage_text"] or ""
        block = (r["block_type"] or "paragraph").lower()
        density = float(r["math_density"] or 0.0)

        text_score = _score(f"{title} {summary} {ptext}", tokens)
        if text_score < 0.5:
            continue

        # Math-aware boost: theorem/definition/proof-like passages and denser symbolic text.
        block_boost = 0.0
        if block in {"theorem", "definition", "proof"}:
            block_boost = 0.12
        elif block == "example":
            block_boost = 0.05

        density_boost = min(0.15, density * 0.8)
        final = min(1.0, text_score + block_boost + density_boost)

        current = best_by_work.get(work_id)
        candidate = {
            "work_id": work_id,
            "title": title,
            "summary": summary[:500],
            "category": r["category"],
            "published": r["published"],
            "updated": r["updated"],
            "score": round(final, 4),
            "source": "arxiv",
            "top_block_type": block,
            "math_density": round(density, 4),
        }
        if current is None or candidate["score"] > current["score"]:
            best_by_work[work_id] = candidate

    scored = sorted(best_by_work.values(), key=lambda x: x["score"], reverse=True)
    return scored[: max(1, req.limit)]


# MVP retrieval: prefer local lexical index; fallback demo while index is empty.
def search(req: SearchRequest) -> list[dict]:
    real = _search_sqlite(req)
    if real:
        return real

    q = req.query.lower()
    if "algebraic geometry" in q or "scheme" in q or "cohomology" in q:
        return [
            {
                "work_id": "arxiv:math.AG-demo-001",
                "title": "Foundational Topics in Algebraic Geometry (demo)",
                "summary": "Fallback demo result before lexical index is built.",
                "category": "math.AG",
                "published": None,
                "updated": None,
                "score": 0.91,
                "source": "arxiv",
                "top_block_type": "paragraph",
                "math_density": 0.0,
            }
        ]
    return []
