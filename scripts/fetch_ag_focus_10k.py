#!/usr/bin/env python3
"""Fetch a focused subset of math.AG papers filtered by key subarea terms."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from mathfoundry.arxiv import dir_size_bytes, fetch_feed, parse_entries, parse_total

FOCUS_TERMS = [
    "moduli",
    "intersection theory",
    "complex algebraic geometry",
    "abelian variety",
]


def focus_query() -> str:
    ors = " OR ".join([f'all:"{t}"' if " " in t else f"all:{t}" for t in FOCUS_TERMS])
    return f"cat:math.AG AND ({ors})"


def main() -> None:
    target = int(os.getenv("MATHFOUNDRY_FOCUS_TARGET", "10000"))
    page_size = int(os.getenv("MATHFOUNDRY_FOCUS_PAGE_SIZE", "200"))
    max_pages = int(os.getenv("MATHFOUNDRY_FOCUS_MAX_PAGES", "1000000"))
    sleep_sec = float(os.getenv("MATHFOUNDRY_FOCUS_SLEEP_SEC", "1.0"))
    checkpoint_every = int(os.getenv("MATHFOUNDRY_FOCUS_CHECKPOINT_EVERY", "2"))
    storage_budget_gb = int(os.getenv("MATHFOUNDRY_STORAGE_BUDGET_GB", "400"))
    stop_ratio = float(os.getenv("MATHFOUNDRY_FOCUS_STOP_RATIO", "0.9"))

    query = focus_query()

    first = fetch_feed(query, start=0, page_size=1)
    total_available = parse_total(first)
    to_fetch = min(target, total_available)

    out_dir = Path("data/topic")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"ag_focus_{to_fetch}_{ts}.jsonl"
    checkpoint_file = out_dir / f"ag_focus_checkpoint_{ts}.json"

    kept = 0
    pages_done = 0
    seen: set[str] = set()

    with out_file.open("w", encoding="utf-8") as f:
        for start in range(0, to_fetch, page_size):
            if pages_done >= max_pages:
                break

            data_dir_size = dir_size_bytes(Path("data"))
            budget_limit = int(storage_budget_gb * stop_ratio * (1024**3))
            if data_dir_size >= budget_limit:
                print(json.dumps({"event": "stop_storage_guard", "data_bytes": data_dir_size, "budget_limit_bytes": budget_limit}))
                break

            xml = fetch_feed(query, start=start, page_size=page_size)
            entries = parse_entries(xml)
            if not entries:
                break

            for entry in entries:
                wid = entry["work_id"]
                if wid in seen:
                    continue
                seen.add(wid)
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                kept += 1

            pages_done += 1
            if pages_done % checkpoint_every == 0:
                ck = {
                    "query": query,
                    "total_available": total_available,
                    "target_requested": target,
                    "saved": str(out_file),
                    "kept": kept,
                    "pages_done": pages_done,
                    "last_start": start,
                    "data_dir_bytes": dir_size_bytes(Path("data")),
                }
                checkpoint_file.write_text(json.dumps(ck, indent=2), encoding="utf-8")
                print(json.dumps({"event": "checkpoint", **ck}))

            time.sleep(sleep_sec)

    print(json.dumps({
        "query": query,
        "total_available": total_available,
        "target_requested": target,
        "saved": str(out_file),
        "checkpoint": str(checkpoint_file),
        "kept": kept,
        "pages_done": pages_done,
        "data_dir_bytes": dir_size_bytes(Path("data")),
    }))


if __name__ == "__main__":
    main()
