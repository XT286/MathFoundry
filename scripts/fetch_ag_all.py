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
    for _ in range(30):
        with httpx.Client(timeout=90.0, follow_redirects=True, headers={"User-Agent": "MathFoundry/0.1 (full AG ingest)"}) as c:
            r = c.get(url)
            if r.status_code == 429:
                time.sleep(delay)
                delay = min(delay * 1.5, 180)
                continue
            r.raise_for_status()
            return r.text
    raise RuntimeError("rate-limited repeatedly; retry later")


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


def dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def main() -> None:
    query = os.getenv("MATHFOUNDRY_ALL_AG_QUERY", "cat:math.AG")
    page_size = int(os.getenv("MATHFOUNDRY_ALL_AG_PAGE_SIZE", "200"))
    sleep_sec = float(os.getenv("MATHFOUNDRY_ALL_AG_SLEEP_SEC", "1.5"))
    checkpoint_every = int(os.getenv("MATHFOUNDRY_ALL_AG_CHECKPOINT_EVERY", "5"))
    max_pages = int(os.getenv("MATHFOUNDRY_ALL_AG_MAX_PAGES", "1000000"))
    storage_budget_gb = int(os.getenv("MATHFOUNDRY_STORAGE_BUDGET_GB", "400"))
    stop_ratio = float(os.getenv("MATHFOUNDRY_ALL_AG_STOP_RATIO", "0.9"))

    out_dir = Path("data/topic")
    out_dir.mkdir(parents=True, exist_ok=True)

    ck_path = out_dir / "ag_all_checkpoint.json"
    out_path = out_dir / "ag_all_math_ag.jsonl"

    if ck_path.exists():
        ck = json.loads(ck_path.read_text(encoding="utf-8"))
        start = int(ck.get("next_start", 0))
        total_available = int(ck.get("total_available", 0))
        kept = int(ck.get("kept", 0))
        pages_done = int(ck.get("pages_done", 0))
        mode = "a"
    else:
        first = fetch_feed(start=0, page_size=1, query=query)
        total_available = parse_total(first)
        start = 0
        kept = 0
        pages_done = 0
        mode = "w"

    with out_path.open(mode, encoding="utf-8") as f:
        while start < total_available and pages_done < max_pages:
            data_bytes = dir_size_bytes(Path("data"))
            if data_bytes >= int(storage_budget_gb * stop_ratio * (1024**3)):
                print(json.dumps({"event": "stop_storage_guard", "data_bytes": data_bytes}))
                break

            xml = fetch_feed(start=start, page_size=page_size, query=query)
            entries = parse_entries(xml)
            if not entries:
                break

            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
                kept += 1

            pages_done += 1
            start += page_size

            if pages_done % checkpoint_every == 0:
                ck = {
                    "query": query,
                    "total_available": total_available,
                    "next_start": start,
                    "kept": kept,
                    "pages_done": pages_done,
                    "updated_at": datetime.now(UTC).isoformat(),
                    "data_dir_bytes": dir_size_bytes(Path("data")),
                    "output": str(out_path),
                }
                ck_path.write_text(json.dumps(ck, indent=2), encoding="utf-8")
                print(json.dumps({"event": "checkpoint", **ck}))

            time.sleep(sleep_sec)

    final = {
        "query": query,
        "total_available": total_available,
        "next_start": start,
        "kept": kept,
        "pages_done": pages_done,
        "output": str(out_path),
        "checkpoint": str(ck_path),
    }
    ck_path.write_text(json.dumps(final, indent=2), encoding="utf-8")
    print(json.dumps(final))


if __name__ == "__main__":
    main()
