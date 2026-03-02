#!/usr/bin/env python3
"""Fetch a small ArXiv slice for local smoke testing."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from mathfoundry.arxiv import fetch_feed
from mathfoundry.config import CONFIG


def main() -> None:
    category = CONFIG.arxiv_primary_category
    query = f"cat:{category}"
    target_bytes = 1 * 1024 * 1024 * 1024  # 1 GB cap
    page_size = 500
    max_pages = 6

    out_dir = Path(CONFIG.data_dir) / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    saved = 0
    for i in range(max_pages):
        start = i * page_size
        xml = fetch_feed(query, start=start, page_size=page_size, sort_by="lastUpdatedDate")
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
