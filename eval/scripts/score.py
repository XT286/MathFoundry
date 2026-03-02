#!/usr/bin/env python3
"""Score evaluation results and write summary.json."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from mathfoundry.io_utils import load_jsonl

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
OUT = RESULTS_DIR / "summary.json"


def main() -> None:
    systems = ["s0_pure_llm", "s1_plain_rag", "s2_rag_verify"]
    summary = {}

    for s in systems:
        rows = load_jsonl(RESULTS_DIR / f"{s}.jsonl")
        if not rows:
            summary[s] = {"count": 0}
            continue

        overclaim = [1 if r.get("overclaim", False) else 0 for r in rows]
        abst_ok = [1 if r.get("abstention_correct", False) else 0 for r in rows if r.get("abstained") is not None]
        corr = [float(r.get("correctness", 0.0)) for r in rows if r.get("correctness") is not None]
        citp = [float(r.get("citation_precision", 0.0)) for r in rows if r.get("citation_precision") is not None]

        summary[s] = {
            "count": len(rows),
            "mean_correctness": round(mean(corr), 4) if corr else None,
            "mean_citation_precision": round(mean(citp), 4) if citp else None,
            "overclaim_rate": round(sum(overclaim) / len(overclaim), 4) if overclaim else None,
            "abstention_correct_rate": round(sum(abst_ok) / len(abst_ok), 4) if abst_ok else None,
        }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"saved": str(OUT), "systems": list(summary.keys())}))


if __name__ == "__main__":
    main()
