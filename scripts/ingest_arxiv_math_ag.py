#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.parse
from datetime import datetime, UTC
from pathlib import Path

import httpx

from mathfoundry.config import CONFIG

ARXIV_API = "https://export.arxiv.org/api/query"


def fetch_category(limit: int) -> str:
    query = f"cat:{CONFIG.arxiv_primary_category}"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max(1, min(limit, CONFIG.max_results_per_ingest)),
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    with httpx.Client(timeout=30.0, follow_redirects=True) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def prune_old_files(raw_dir: Path, keep: int) -> int:
    files = sorted(raw_dir.glob("arxiv_*.xml"), key=lambda p: p.stat().st_mtime, reverse=True)
    deleted = 0
    for f in files[keep:]:
        f.unlink(missing_ok=True)
        deleted += 1
    return deleted


def main() -> None:
    raw = fetch_category(limit=CONFIG.max_results_per_ingest)

    out_dir = Path(CONFIG.data_dir) / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"arxiv_{CONFIG.arxiv_primary_category.replace('.', '_')}_{ts}.xml"
    out_file.write_text(raw, encoding="utf-8")

    deleted = prune_old_files(out_dir, keep=max(1, CONFIG.max_raw_files))

    print(
        json.dumps(
            {
                "saved": str(out_file),
                "bytes": len(raw),
                "category": CONFIG.arxiv_primary_category,
                "max_results_per_ingest": CONFIG.max_results_per_ingest,
                "max_raw_files": CONFIG.max_raw_files,
                "deleted_old_files": deleted,
            }
        )
    )


if __name__ == "__main__":
    main()
