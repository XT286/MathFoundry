#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark" / "queries.jsonl"
RESULTS = ROOT / "results"


def load_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def call_json(client: httpx.Client, url: str, payload: dict) -> dict:
    r = client.post(url, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def main() -> None:
    p = argparse.ArgumentParser(description="Run baseline comparison scaffold")
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--queries", default=str(BENCH))
    p.add_argument("--limit", type=int, default=0, help="0 means all")
    args = p.parse_args()

    queries = load_jsonl(Path(args.queries))
    if args.limit > 0:
        queries = queries[: args.limit]

    s2_rows: list[dict] = []
    s0_template: list[dict] = []

    with httpx.Client() as client:
        for q in queries:
            qid = q.get("id")
            query = q["query"]

            search = call_json(client, f"{args.base_url}/search", {"query": query, "limit": 8})
            qa = call_json(client, f"{args.base_url}/qa", {"query": query, "mode": "brief"})
            ver = call_json(client, f"{args.base_url}/qa/verify", {"answer": qa})

            s2_rows.append(
                {
                    "id": qid,
                    "query": query,
                    "system": "s2_rag_verify",
                    "answer": qa.get("answer_summary"),
                    "confidence": qa.get("confidence"),
                    "claims": len(qa.get("claims", [])),
                    "references": len(qa.get("references", [])),
                    "search_count": search.get("count", 0),
                    "verify_ok": ver.get("ok"),
                    "coverage_ratio": ver.get("coverage_ratio"),
                    "must_abstain": ver.get("must_abstain"),
                    "correctness": None,
                    "citation_precision": None,
                    "overclaim": None,
                    "abstained": bool(ver.get("must_abstain")),
                    "abstention_correct": None,
                    "notes": "Fill rubric fields after human review.",
                }
            )

            s0_template.append(
                {
                    "id": qid,
                    "query": query,
                    "system": "s0_pure_llm",
                    "answer": "",
                    "citations": [],
                    "correctness": None,
                    "citation_precision": None,
                    "overclaim": None,
                    "abstained": None,
                    "abstention_correct": None,
                    "notes": "Paste pure LLM answer here, then score with reviewer rubric.",
                }
            )

    write_jsonl(RESULTS / "s2_rag_verify.jsonl", s2_rows)
    write_jsonl(RESULTS / "s0_pure_llm_template.jsonl", s0_template)

    print(
        json.dumps(
            {
                "queries": len(queries),
                "saved": [
                    str(RESULTS / "s2_rag_verify.jsonl"),
                    str(RESULTS / "s0_pure_llm_template.jsonl"),
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
