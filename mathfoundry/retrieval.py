from __future__ import annotations

import re
import sqlite3

from .indexing import db_path
from .models import SearchRequest


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9*\-]+", text.lower()) if len(t) >= 2]


def _score(title: str, summary: str, tokens: list[str]) -> float:
    hay = f"{title} {summary}".lower()
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

    # broad pull then local scoring for deterministic lightweight lexical behavior
    rows = conn.execute(
        "SELECT work_id,title,summary,category,published,updated FROM papers ORDER BY updated DESC LIMIT 1200"
    ).fetchall()
    conn.close()

    scored = []
    for r in rows:
        s = _score(r["title"] or "", r["summary"] or "", tokens)
        if s > 0:
            scored.append(
                {
                    "work_id": r["work_id"],
                    "title": r["title"],
                    "summary": (r["summary"] or "")[:500],
                    "category": r["category"],
                    "published": r["published"],
                    "updated": r["updated"],
                    "score": round(float(s), 4),
                    "source": "arxiv",
                }
            )

    scored.sort(key=lambda x: x["score"], reverse=True)
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
            }
        ]
    return []
