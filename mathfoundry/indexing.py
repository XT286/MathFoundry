from __future__ import annotations

import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET

from .config import CONFIG

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def db_path() -> Path:
    return Path(CONFIG.data_dir) / "index" / "mathfoundry.db"


def ensure_db() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS papers (
          work_id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          summary TEXT,
          category TEXT,
          published TEXT,
          updated TEXT,
          source_file TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_category ON papers(category)")
    conn.commit()
    return conn


def parse_arxiv_atom(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    out: list[dict] = []
    for e in root.findall("atom:entry", ATOM_NS):
        id_text = (e.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        title = " ".join((e.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
        summary = " ".join((e.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").split())
        published = (e.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        updated = (e.findtext("atom:updated", default="", namespaces=ATOM_NS) or "").strip()

        primary_cat = None
        for c in e.findall("atom:category", ATOM_NS):
            term = c.attrib.get("term")
            if term and term.startswith("math."):
                primary_cat = term
                break
        work_id = id_text.replace("http://arxiv.org/abs/", "arxiv:").replace("https://arxiv.org/abs/", "arxiv:")
        if work_id and title:
            out.append(
                {
                    "work_id": work_id,
                    "title": title,
                    "summary": summary,
                    "category": primary_cat,
                    "published": published,
                    "updated": updated,
                }
            )
    return out


def index_raw_file(xml_file: Path) -> int:
    text = xml_file.read_text(encoding="utf-8")
    rows = parse_arxiv_atom(text)
    if not rows:
        return 0
    conn = ensure_db()
    with conn:
        conn.executemany(
            """
            INSERT INTO papers(work_id, title, summary, category, published, updated, source_file)
            VALUES(:work_id,:title,:summary,:category,:published,:updated,:source_file)
            ON CONFLICT(work_id) DO UPDATE SET
              title=excluded.title,
              summary=excluded.summary,
              category=excluded.category,
              published=excluded.published,
              updated=excluded.updated,
              source_file=excluded.source_file
            """,
            [{**r, "source_file": str(xml_file)} for r in rows],
        )
    conn.close()
    return len(rows)


def index_all_raw() -> int:
    raw_dir = Path(CONFIG.data_dir) / "raw"
    if not raw_dir.exists():
        return 0
    total = 0
    for xml_file in sorted(raw_dir.glob("arxiv_*.xml")):
        total += index_raw_file(xml_file)
    return total
