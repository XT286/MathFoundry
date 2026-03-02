#!/usr/bin/env python3
"""Background worker: periodically ingest new ArXiv data and rebuild the index."""

from __future__ import annotations

import os
import subprocess
import sys
import time


def main() -> None:
    interval_min = int(os.getenv("MATHFOUNDRY_INGEST_INTERVAL_MIN", "180"))
    python = sys.executable
    while True:
        subprocess.run([python, "scripts/ingest_arxiv_math_ag.py"], check=False)
        subprocess.run([python, "scripts/build_lexical_index.py"], check=False)
        time.sleep(max(60, interval_min * 60))


if __name__ == "__main__":
    main()
