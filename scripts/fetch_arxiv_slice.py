#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.parse
from datetime import datetime, UTC
from pathlib import Path

import httpx

from mathfoundry.config import CONFIG

ARXIV_API = "https://export.arxiv.org/api/query"


def fetch_page(category: str, start: int, page_size: int) -> str:
    params = {
        "search_query": f"cat:{category}",
        "start": start,
        "max_results": page_size,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    with httpx.Client(timeout=45.0, follow_redirects=True) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def main() -> None:
    category = CONFIG.arxiv_primary_category
    target_bytes = 1 * 1024 * 1024 * 1024  # 1GB cap (upper bound)
    page_size = 500
    max_pages = 6  # keep local smoke practical

    out_dir = Path(CONFIG.data_dir) / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    saved = 0
    for i in range(max_pages):
        start = i * page_size
        xml = fetch_page(category, start=start, page_size=page_size)
        b = len(xml.encode("utf-8"))
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        f = out_dir / f"arxiv_slice_{category.replace('.', '_')}_{start}_{ts}.xml"
        f.write_text(xml, encoding="utf-8")
        saved += 1
        total += b
        if total >= target_bytes:
            break

    print(json.dumps({"category": category, "files_saved": saved, "bytes_saved": total, "target_cap_bytes": target_bytes}))


if __name__ == "__main__":
    main()
