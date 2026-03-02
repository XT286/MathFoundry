#!/usr/bin/env python3
"""Fetch recent math.AG papers from ArXiv and prune old raw files."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from mathfoundry.arxiv import fetch_feed
from mathfoundry.config import CONFIG


def prune_old_files(raw_dir: Path, keep: int) -> int:
    files = sorted(raw_dir.glob("arxiv_*.xml"), key=lambda p: p.stat().st_mtime, reverse=True)
    deleted = 0
    for f in files[keep:]:
        f.unlink(missing_ok=True)
        deleted += 1
    return deleted


def main() -> None:
    category = CONFIG.arxiv_primary_category
    query = f"cat:{category}"
    limit = CONFIG.max_results_per_ingest

    raw = fetch_feed(
        query,
        start=0,
        page_size=max(1, min(limit, CONFIG.max_results_per_ingest)),
        sort_by="lastUpdatedDate",
    )

    out_dir = Path(CONFIG.data_dir) / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"arxiv_{category.replace('.', '_')}_{ts}.xml"
    out_file.write_text(raw, encoding="utf-8")

    deleted = prune_old_files(out_dir, keep=max(1, CONFIG.max_raw_files))

    print(
        json.dumps(
            {
                "saved": str(out_file),
                "bytes": len(raw),
                "category": category,
                "max_results_per_ingest": CONFIG.max_results_per_ingest,
                "max_raw_files": CONFIG.max_raw_files,
                "deleted_old_files": deleted,
            }
        )
    )


if __name__ == "__main__":
    main()
