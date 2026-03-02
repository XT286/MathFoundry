"""Shared ArXiv API helpers for fetching and parsing Atom feeds."""

from __future__ import annotations

import random
import time
import urllib.parse
import xml.etree.ElementTree as ET

import httpx

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}

_USER_AGENT = "MathFoundry/0.1 (research indexing)"


def fetch_feed(
    query: str,
    start: int,
    page_size: int,
    *,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
    timeout: float = 90.0,
    max_retries: int = 40,
) -> str:
    """Fetch an ArXiv Atom feed page with exponential-backoff retry."""
    params = {
        "search_query": query,
        "start": start,
        "max_results": page_size,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"

    delay = 5.0
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT},
    ) as client:
        for _attempt in range(1, max_retries + 1):
            try:
                r = client.get(url)
            except httpx.HTTPError:
                time.sleep(delay + random.uniform(0.0, 2.0))
                delay = min(delay * 1.5, 240)
                continue

            if r.status_code == 429 or 500 <= r.status_code <= 599:
                time.sleep(delay + random.uniform(0.0, 2.0))
                delay = min(delay * 1.5, 240)
                continue

            r.raise_for_status()
            return r.text

    raise RuntimeError(f"fetch failed after {max_retries} retries (start={start}, page_size={page_size})")


def parse_total(xml_text: str) -> int:
    """Extract opensearch:totalResults from an Atom feed."""
    root = ET.fromstring(xml_text)
    t = root.findtext("opensearch:totalResults", default="0", namespaces=ATOM_NS)
    try:
        return int(t)
    except (ValueError, TypeError):
        return 0


def parse_entries(xml_text: str, default_category: str = "math.AG") -> list[dict]:
    """Parse Atom entries into normalised dicts."""
    root = ET.fromstring(xml_text)
    out: list[dict] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        raw_id = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
        summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").split())
        updated = (entry.findtext("atom:updated", default="", namespaces=ATOM_NS) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()

        work_id = raw_id.replace("http://arxiv.org/abs/", "arxiv:").replace("https://arxiv.org/abs/", "arxiv:")

        # Try to detect the primary math category from the feed entry.
        category = default_category
        for cat_el in entry.findall("atom:category", ATOM_NS):
            term = cat_el.attrib.get("term", "")
            if term.startswith("math."):
                category = term
                break

        if work_id and title:
            out.append(
                {
                    "work_id": work_id,
                    "title": title,
                    "summary": summary,
                    "updated": updated,
                    "published": published,
                    "category": category,
                }
            )
    return out


def dir_size_bytes(path: "Path") -> int:  # noqa: F821 – Path imported by callers
    """Total bytes of all files under *path* (non-recursive import to avoid circular deps)."""
    from pathlib import Path as _Path

    p = _Path(path)
    if not p.exists():
        return 0
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
