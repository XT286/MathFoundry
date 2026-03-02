#!/usr/bin/env python3
"""Run RAG + verify evaluation where the generation step uses OpenAI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import httpx

from mathfoundry.io_utils import load_jsonl, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUERIES = ROOT / "benchmark" / "ag_queries_v1.jsonl"
DEFAULT_OUT = ROOT / "results" / "s2_rag_verify.jsonl"


def openai_answer_with_context(client: httpx.Client, model: str, query: str, refs: list[dict]) -> str:
    context_lines = []
    for i, r in enumerate(refs[:5], start=1):
        context_lines.append(
            f"[{i}] work_id={r.get('work_id')} | title={r.get('title')} | summary={r.get('summary')}"
        )
    context = "\n".join(context_lines)

    prompt = (
        "You are a math literature assistant. Use ONLY the provided references. "
        "Write a concise answer summary (3-6 sentences). If evidence is weak, say so.\n\n"
        f"Query: {query}\n\n"
        f"References:\n{context}\n"
    )
    r = client.post(
        "https://api.openai.com/v1/responses",
        json={"model": model, "input": prompt},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    # Responses API: output -> [message] -> content -> [output_text] -> text
    for msg in data.get("output", []):
        for block in msg.get("content", []):
            if block.get("type") == "output_text":
                return block.get("text", "").strip()
    return ""


def main() -> None:
    p = argparse.ArgumentParser(description="Run RAG(+verify) where generation uses OpenAI")
    p.add_argument("--model", default="gpt-4.1")
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
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

    openai_headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    out_rows: list[dict] = []

    with httpx.Client() as app_client, httpx.Client(headers=openai_headers) as oai_client:
        for q in queries:
            query = q["query"]
            s = app_client.post(f"{args.base_url}/search", json={"query": query, "limit": 8}, timeout=60)
            s.raise_for_status()
            search = s.json()
            refs = search.get("results", [])

            answer_summary = openai_answer_with_context(oai_client, args.model, query, refs)

            grounded = {
                "answer_summary": answer_summary,
                "claims": [
                    {
                        "text": "The answer is grounded in top retrieved references for this query.",
                        "supporting_citations": [{"work_id": refs[0].get("work_id")}] if refs else [],
                        "support_level": "direct",
                    }
                ] if refs else [],
                "references": refs[:5],
                "confidence": "low" if refs else "insufficient_evidence",
                "limitations": ["LLM-generated synthesis; human review recommended."],
                "query_refinements": [],
            }

            v = app_client.post(f"{args.base_url}/qa/verify", json={"answer": grounded}, timeout=60)
            v.raise_for_status()
            ver = v.json()

            out_rows.append(
                {
                    "id": q.get("id"),
                    "query": query,
                    "system": "s2_rag_verify",
                    "model": args.model,
                    "answer": answer_summary,
                    "confidence": grounded.get("confidence"),
                    "claims": len(grounded.get("claims", [])),
                    "references": len(grounded.get("references", [])),
                    "search_count": search.get("count", 0),
                    "verify_ok": ver.get("ok"),
                    "coverage_ratio": ver.get("coverage_ratio"),
                    "must_abstain": ver.get("must_abstain"),
                    "correctness": None,
                    "citation_precision": None,
                    "overclaim": None,
                    "abstained": bool(ver.get("must_abstain")),
                    "abstention_correct": None,
                    "notes": "RAG with OpenAI generation; requires human rubric review",
                }
            )

    write_jsonl(Path(args.out), out_rows)
    print(json.dumps({"queries": len(out_rows), "model": args.model, "saved": str(Path(args.out))}))


if __name__ == "__main__":
    main()
