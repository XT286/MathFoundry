from __future__ import annotations

import re
import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET

from .config import CONFIG
from .subareas import detect_ag_subareas

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
_BLOCK_MARKERS = {
    "theorem": ["theorem", "lemma", "proposition", "corollary"],
    "definition": ["definition", "notion", "denote"],
    "proof": ["proof", "sketch", "argument"],
    "example": ["example", "counterexample"],
}


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
          ag_subareas TEXT,
          published TEXT,
          updated TEXT,
          source_file TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_category ON papers(category)")
    # lightweight migration for existing local DBs
    try:
        conn.execute("ALTER TABLE papers ADD COLUMN ag_subareas TEXT")
    except sqlite3.OperationalError:
        pass

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS passages (
          passage_id TEXT PRIMARY KEY,
          work_id TEXT NOT NULL,
          chunk_index INTEGER NOT NULL,
          section_label TEXT,
          block_type TEXT,
          text TEXT NOT NULL,
          math_density REAL NOT NULL,
          token_est INTEGER NOT NULL,
          FOREIGN KEY(work_id) REFERENCES papers(work_id)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_passages_work ON passages(work_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_passages_block ON passages(block_type)")
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


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _math_density(text: str) -> float:
    if not text:
        return 0.0
    mathish = re.findall(r"[\\$^_{}]|\\[a-zA-Z]+|\b[A-Z][a-zA-Z]?\b", text)
    return round(min(1.0, len(mathish) / max(1, len(text))), 4)


def _detect_block_type(text: str) -> str:
    t = text.lower()
    for block, markers in _BLOCK_MARKERS.items():
        if any(m in t for m in markers):
            return block
    return "paragraph"


def _split_passages(summary: str, work_id: str) -> list[dict]:
    # Sentence-based chunking with lightweight math-aware metadata.
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", summary) if p.strip()]
    if not parts:
        parts = [summary.strip()] if summary.strip() else []

    chunks: list[dict] = []
    current = ""
    chunk_index = 0
    for s in parts:
        if len((current + " " + s).strip()) > 900 and current:
            text = current.strip()
            chunks.append(
                {
                    "passage_id": f"{work_id}#p{chunk_index}",
                    "work_id": work_id,
                    "chunk_index": chunk_index,
                    "section_label": "abstract",
                    "block_type": _detect_block_type(text),
                    "text": text,
                    "math_density": _math_density(text),
                    "token_est": _estimate_tokens(text),
                }
            )
            chunk_index += 1
            current = s
        else:
            current = (current + " " + s).strip()

    if current:
        text = current.strip()
        chunks.append(
            {
                "passage_id": f"{work_id}#p{chunk_index}",
                "work_id": work_id,
                "chunk_index": chunk_index,
                "section_label": "abstract",
                "block_type": _detect_block_type(text),
                "text": text,
                "math_density": _math_density(text),
                "token_est": _estimate_tokens(text),
            }
        )
    return chunks


def index_raw_file(xml_file: Path) -> int:
    text = xml_file.read_text(encoding="utf-8")
    rows = parse_arxiv_atom(text)
    if not rows:
        return 0

    conn = ensure_db()
    with conn:
        payload_rows = []
        for r in rows:
            tags = detect_ag_subareas(f"{r.get('title','')} {r.get('summary','')}") if r.get("category") == "math.AG" else []
            payload_rows.append({**r, "source_file": str(xml_file), "ag_subareas": ",".join(tags)})

        conn.executemany(
            """
            INSERT INTO papers(work_id, title, summary, category, ag_subareas, published, updated, source_file)
            VALUES(:work_id,:title,:summary,:category,:ag_subareas,:published,:updated,:source_file)
            ON CONFLICT(work_id) DO UPDATE SET
              title=excluded.title,
              summary=excluded.summary,
              category=excluded.category,
              ag_subareas=excluded.ag_subareas,
              published=excluded.published,
              updated=excluded.updated,
              source_file=excluded.source_file
            """,
            payload_rows,
        )

        for r in rows:
            conn.execute("DELETE FROM passages WHERE work_id = ?", (r["work_id"],))
            passages = _split_passages(r.get("summary", ""), r["work_id"])
            if passages:
                conn.executemany(
                    """
                    INSERT INTO passages(passage_id, work_id, chunk_index, section_label, block_type, text, math_density, token_est)
                    VALUES(:passage_id,:work_id,:chunk_index,:section_label,:block_type,:text,:math_density,:token_est)
                    """,
                    passages,
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
