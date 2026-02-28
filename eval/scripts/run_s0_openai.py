#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUERIES = ROOT / "benchmark" / "ag_queries_v1.jsonl"
DEFAULT_OUT = ROOT / "results" / "s0_pure_llm.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def openai_response(client: httpx.Client, model: str, query: str) -> str:
    prompt = (
        "You are a mathematical research assistant. Answer the user query concisely. "
        "If uncertain, say so explicitly. Do not fabricate citations.\n\n"
        f"Query: {query}"
    )
    r = client.post(
        "https://api.openai.com/v1/responses",
        json={"model": model, "input": prompt},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    return (data.get("output_text") or "").strip()


def main() -> None:
    p = argparse.ArgumentParser(description="Generate pure-LLM baseline with OpenAI Responses API")
    p.add_argument("--model", default="gpt-4.1")
    p.add_argument("--queries", default=str(DEFAULT_QUERIES))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required")

    queries = load_jsonl(Path(args.queries))
    if args.limit > 0:
        queries = queries[: args.limit]

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    rows: list[dict] = []

    with httpx.Client(headers=headers) as client:
        for q in queries:
            query = q["query"]
            ans = openai_response(client, args.model, query)
            rows.append(
                {
                    "id": q.get("id"),
                    "query": query,
                    "system": "s0_pure_llm",
                    "model": args.model,
                    "answer": ans,
                    "citations": [],
                    "correctness": None,
                    "citation_precision": 0.0,
                    "overclaim": True,
                    "abstained": False,
                    "abstention_correct": None,
                    "notes": "auto-generated via OpenAI API; requires human rubric review",
                }
            )

    write_jsonl(Path(args.out), rows)
    print(json.dumps({"queries": len(rows), "model": args.model, "saved": str(Path(args.out))}))


if __name__ == "__main__":
    main()
