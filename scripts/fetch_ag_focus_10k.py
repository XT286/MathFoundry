#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import httpx

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}

FOCUS_TERMS = [
    "moduli",
    "intersection theory",
    "complex algebraic geometry",
    "abelian variety",
]


def focus_query() -> str:
    ors = " OR ".join([f'all:"{t}"' if " " in t else f"all:{t}" for t in FOCUS_TERMS])
    return f"cat:math.AG AND ({ors})"


def fetch_feed(start: int, page_size: int, query: str) -> str:
    params = {
        "search_query": query,
        "start": start,
        "max_results": page_size,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"

    delay = 5.0
    for _ in range(20):
        with httpx.Client(timeout=60.0, follow_redirects=True, headers={"User-Agent": "MathFoundry/0.1 (research indexing; contact: local-dev)"}) as c:
            r = c.get(url)
            if r.status_code == 429:
                time.sleep(delay)
                delay = min(delay * 1.5, 120)
                continue
            r.raise_for_status()
            return r.text

    raise RuntimeError("rate-limited; retry later")


def parse_total(xml_text: str) -> int:
    root = ET.fromstring(xml_text)
    t = root.findtext("opensearch:totalResults", default="0", namespaces=ATOM_NS)
    try:
        return int(t)
    except Exception:
        return 0


def parse_entries(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    out: list[dict] = []
    for e in root.findall("atom:entry", ATOM_NS):
        aid = (e.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        title = " ".join((e.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
        summary = " ".join((e.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").split())
        updated = (e.findtext("atom:updated", default="", namespaces=ATOM_NS) or "").strip()
        published = (e.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        out.append(
            {
                "work_id": aid.replace("http://arxiv.org/abs/", "arxiv:").replace("https://arxiv.org/abs/", "arxiv:"),
                "title": title,
                "summary": summary,
                "updated": updated,
                "published": published,
                "category": "math.AG",
            }
        )
    return out


def _dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def main() -> None:
    target = int(os.getenv('MATHFOUNDRY_FOCUS_TARGET', '10000'))
    page_size = int(os.getenv('MATHFOUNDRY_FOCUS_PAGE_SIZE', '200'))
    max_pages = int(os.getenv('MATHFOUNDRY_FOCUS_MAX_PAGES', '1000000'))
    sleep_sec = float(os.getenv('MATHFOUNDRY_FOCUS_SLEEP_SEC', '1.0'))
    checkpoint_every = int(os.getenv('MATHFOUNDRY_FOCUS_CHECKPOINT_EVERY', '2'))
    storage_budget_gb = int(os.getenv('MATHFOUNDRY_STORAGE_BUDGET_GB', '400'))
    stop_ratio = float(os.getenv('MATHFOUNDRY_FOCUS_STOP_RATIO', '0.9'))

    query = focus_query()

    first = fetch_feed(start=0, page_size=1, query=query)
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

            data_dir_size = _dir_size_bytes(Path("data"))
            budget_limit = int(storage_budget_gb * stop_ratio * (1024**3))
            if data_dir_size >= budget_limit:
                print(json.dumps({"event": "stop_storage_guard", "data_bytes": data_dir_size, "budget_limit_bytes": budget_limit}))
                break

            xml = fetch_feed(start=start, page_size=page_size, query=query)
            entries = parse_entries(xml)
            if not entries:
                break
            for e in entries:
                wid = e["work_id"]
                if wid in seen:
                    continue
                seen.add(wid)
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
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
                    "data_dir_bytes": _dir_size_bytes(Path("data")),
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
        "data_dir_bytes": _dir_size_bytes(Path("data")),
    }))


if __name__ == "__main__":
    main()
