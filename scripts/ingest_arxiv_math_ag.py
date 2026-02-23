#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

import httpx

from mathfoundry.config import CONFIG

ARXIV_API = "http://export.arxiv.org/api/query"


def fetch_math_ag(limit: int = 25) -> str:
    query = f"cat:{CONFIG.arxiv_primary_category}"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": limit,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    with httpx.Client(timeout=20.0) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def main() -> None:
    raw = fetch_math_ag()
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "arxiv_math_ag_latest.xml"
    out_file.write_text(raw, encoding="utf-8")
    print(json.dumps({"saved": str(out_file), "bytes": len(raw)}))


if __name__ == "__main__":
    main()
