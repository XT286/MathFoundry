#!/usr/bin/env python3
"""Resumable full math.AG ingestion from ArXiv with checkpointing.

Modes:
- offset: classic start/max_results pagination on one query
- slice: date-window slicing + pagination from start=0 per slice (avoids deep offsets)
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from mathfoundry.arxiv import dir_size_bytes, fetch_feed, parse_entries, parse_total


def _date_yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def _parse_yyyymmdd(s: str) -> date:
    return datetime.strptime(s, "%Y%m%d").date()


def _load_existing_ids(path: Path) -> set[str]:
    seen: set[str] = set()
    if not path.exists():
        return seen
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            wid = str(obj.get("work_id", "")).strip()
            if wid:
                seen.add(wid)
    return seen


def main() -> None:
    query = os.getenv("MATHFOUNDRY_ALL_AG_QUERY", "cat:math.AG")
    mode = os.getenv("MATHFOUNDRY_ALL_AG_MODE", "offset").strip().lower()

    page_size = int(os.getenv("MATHFOUNDRY_ALL_AG_PAGE_SIZE", "200"))
    sleep_sec = float(os.getenv("MATHFOUNDRY_ALL_AG_SLEEP_SEC", "1.5"))
    checkpoint_every = int(os.getenv("MATHFOUNDRY_ALL_AG_CHECKPOINT_EVERY", "1"))
    checkpoint_interval_sec = float(os.getenv("MATHFOUNDRY_ALL_AG_CHECKPOINT_INTERVAL_SEC", "30"))
    max_pages = int(os.getenv("MATHFOUNDRY_ALL_AG_MAX_PAGES", "1000000"))
    storage_budget_gb = int(os.getenv("MATHFOUNDRY_STORAGE_BUDGET_GB", "400"))
    stop_ratio = float(os.getenv("MATHFOUNDRY_ALL_AG_STOP_RATIO", "0.9"))
    fetch_timeout = float(os.getenv("MATHFOUNDRY_ALL_AG_FETCH_TIMEOUT_SEC", "60"))
    fetch_max_retries = int(os.getenv("MATHFOUNDRY_ALL_AG_FETCH_MAX_RETRIES", "8"))
    min_page_size = int(os.getenv("MATHFOUNDRY_ALL_AG_MIN_PAGE_SIZE", "10"))
    cooldown_on_error_sec = float(os.getenv("MATHFOUNDRY_ALL_AG_COOLDOWN_ON_ERROR_SEC", "20"))
    max_min_page_failures = int(os.getenv("MATHFOUNDRY_ALL_AG_MAX_MIN_PAGE_FAILURES", "6"))

    slice_days = int(os.getenv("MATHFOUNDRY_ALL_AG_SLICE_DAYS", "30"))
    slice_earliest = os.getenv("MATHFOUNDRY_ALL_AG_SLICE_EARLIEST", "19910101")

    out_dir = Path("data/topic")
    out_dir.mkdir(parents=True, exist_ok=True)

    ck_path = out_dir / "ag_all_checkpoint.json"
    out_path = out_dir / "ag_all_math_ag.jsonl"

    # Shared run state
    pages_done_this_run = 0
    current_page_size = page_size
    last_error = ""
    consecutive_failures = 0
    min_page_failures = 0
    last_checkpoint_ts = 0.0
    run_started = time.time()

    # Resume defaults
    start = 0
    total_available = 0
    kept = 0
    pages_done = 0

    # Slice resume state
    slice_cursor_end = _date_yyyymmdd(datetime.now(UTC).date())
    slice_next_start = 0

    ck: dict = {}
    if ck_path.exists():
        ck = json.loads(ck_path.read_text(encoding="utf-8"))

    if ck and ck.get("mode") == mode:
        start = int(ck.get("next_start", 0))
        total_available = int(ck.get("total_available", 0))
        kept = int(ck.get("kept", 0))
        pages_done = int(ck.get("pages_done", 0))
        current_page_size = int(ck.get("current_page_size", page_size))
        slice_cursor_end = str(ck.get("slice_cursor_end", slice_cursor_end))
        slice_next_start = int(ck.get("slice_next_start", 0))
        print(
            json.dumps(
                {
                    "event": "resume_from_checkpoint",
                    "mode": mode,
                    "next_start": start,
                    "kept": kept,
                    "pages_done": pages_done,
                    "total_available": total_available,
                    "slice_cursor_end": slice_cursor_end,
                    "slice_next_start": slice_next_start,
                }
            ),
            flush=True,
        )
    elif ck and ck.get("mode") and ck.get("mode") != mode:
        print(json.dumps({"event": "checkpoint_mode_mismatch", "old_mode": ck.get("mode"), "new_mode": mode}), flush=True)

    seen_ids = _load_existing_ids(out_path)
    if kept == 0:
        kept = len(seen_ids)

    def write_checkpoint(event: str, extra: dict | None = None) -> None:
        nonlocal last_checkpoint_ts
        payload = {
            "mode": mode,
            "query": query,
            "total_available": total_available,
            "next_start": start,
            "kept": kept,
            "pages_done": pages_done,
            "pages_done_this_run": pages_done_this_run,
            "current_page_size": current_page_size,
            "updated_at": datetime.now(UTC).isoformat(),
            "data_dir_bytes": dir_size_bytes(Path("data")),
            "output": str(out_path),
            "last_error": last_error,
            "slice_days": slice_days,
            "slice_cursor_end": slice_cursor_end,
            "slice_next_start": slice_next_start,
            "event": event,
        }
        if extra:
            payload.update(extra)
        ck_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"event": "checkpoint", **payload}), flush=True)
        last_checkpoint_ts = time.time()

    write_checkpoint("run_started")

    with out_path.open("a", encoding="utf-8") as f:
        if mode == "slice":
            earliest = _parse_yyyymmdd(slice_earliest)
            cursor_end = _parse_yyyymmdd(slice_cursor_end)

            while cursor_end >= earliest and pages_done_this_run < max_pages:
                data_bytes = dir_size_bytes(Path("data"))
                if data_bytes >= int(storage_budget_gb * stop_ratio * (1024**3)):
                    print(json.dumps({"event": "stop_storage_guard", "data_bytes": data_bytes}), flush=True)
                    break

                window_start = max(earliest, cursor_end - timedelta(days=max(1, slice_days) - 1))
                slice_query = (
                    f"{query} AND submittedDate:[{_date_yyyymmdd(window_start)}0000 "
                    f"TO {_date_yyyymmdd(cursor_end)}2359]"
                )

                slice_total = 0
                # For resumed mid-slice, keep slice_next_start; else start at 0.
                if slice_next_start == 0:
                    print(
                        json.dumps(
                            {
                                "event": "slice_start",
                                "slice_start": _date_yyyymmdd(window_start),
                                "slice_end": _date_yyyymmdd(cursor_end),
                                "query": slice_query,
                            }
                        ),
                        flush=True,
                    )

                while pages_done_this_run < max_pages:
                    start = slice_next_start
                    try:
                        xml = fetch_feed(
                            slice_query,
                            start=start,
                            page_size=current_page_size,
                            timeout=fetch_timeout,
                            max_retries=fetch_max_retries,
                            verbose=True,
                        )
                    except RuntimeError as e:
                        last_error = str(e)
                        consecutive_failures += 1

                        if current_page_size > min_page_size:
                            current_page_size = max(min_page_size, current_page_size // 2)
                            print(
                                json.dumps(
                                    {
                                        "event": "page_size_reduce_on_error",
                                        "mode": "slice",
                                        "slice_start": _date_yyyymmdd(window_start),
                                        "slice_end": _date_yyyymmdd(cursor_end),
                                        "start": start,
                                        "new_page_size": current_page_size,
                                        "consecutive_failures": consecutive_failures,
                                        "reason": last_error,
                                    }
                                ),
                                flush=True,
                            )
                            write_checkpoint("page_size_reduce_on_error")
                            if cooldown_on_error_sec > 0:
                                print(json.dumps({"event": "cooldown_on_error", "start": start, "sleep_sec": cooldown_on_error_sec}), flush=True)
                                time.sleep(cooldown_on_error_sec)
                            continue

                        min_page_failures += 1
                        print(
                            json.dumps(
                                {
                                    "event": "min_page_retry_failed",
                                    "mode": "slice",
                                    "start": start,
                                    "page_size": current_page_size,
                                    "min_page_failures": min_page_failures,
                                    "max_min_page_failures": max_min_page_failures,
                                    "reason": last_error,
                                }
                            ),
                            flush=True,
                        )
                        write_checkpoint("min_page_retry_failed")
                        if cooldown_on_error_sec > 0:
                            print(json.dumps({"event": "cooldown_on_error", "start": start, "sleep_sec": cooldown_on_error_sec}), flush=True)
                            time.sleep(cooldown_on_error_sec)
                        if min_page_failures < max_min_page_failures:
                            continue

                        print(json.dumps({"event": "fatal_fetch_error", "mode": "slice", "start": start, "reason": last_error}), flush=True)
                        write_checkpoint("fatal_fetch_error")
                        break

                    entries = parse_entries(xml)
                    slice_total = max(slice_total, parse_total(xml))
                    consecutive_failures = 0
                    min_page_failures = 0

                    if not entries:
                        print(
                            json.dumps(
                                {
                                    "event": "slice_complete_no_entries",
                                    "slice_start": _date_yyyymmdd(window_start),
                                    "slice_end": _date_yyyymmdd(cursor_end),
                                    "slice_next_start": slice_next_start,
                                    "slice_total": slice_total,
                                }
                            ),
                            flush=True,
                        )
                        break

                    written = 0
                    dupes = 0
                    for entry in entries:
                        wid = entry.get("work_id", "")
                        if not wid or wid in seen_ids:
                            dupes += 1
                            continue
                        seen_ids.add(wid)
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        kept += 1
                        written += 1

                    pages_done += 1
                    pages_done_this_run += 1
                    slice_next_start += len(entries)
                    start = slice_next_start
                    total_available = max(total_available, kept)

                    elapsed = max(1e-6, time.time() - run_started)
                    rate = kept / elapsed
                    print(
                        json.dumps(
                            {
                                "event": "progress",
                                "mode": "slice",
                                "slice_start": _date_yyyymmdd(window_start),
                                "slice_end": _date_yyyymmdd(cursor_end),
                                "slice_total": slice_total,
                                "slice_next_start": slice_next_start,
                                "written": written,
                                "dupes": dupes,
                                "kept": kept,
                                "pages_done": pages_done,
                                "pages_done_this_run": pages_done_this_run,
                                "page_size_requested": current_page_size,
                                "entries_returned": len(entries),
                                "rate_records_per_sec": round(rate, 3),
                            }
                        ),
                        flush=True,
                    )

                    if current_page_size < page_size and pages_done_this_run % 10 == 0:
                        current_page_size = min(page_size, current_page_size * 2)
                        print(json.dumps({"event": "page_size_restore", "start": start, "page_size": current_page_size}), flush=True)

                    now = time.time()
                    if pages_done % checkpoint_every == 0 or (now - last_checkpoint_ts) >= checkpoint_interval_sec:
                        write_checkpoint("periodic")

                    if slice_total and slice_next_start >= slice_total:
                        print(
                            json.dumps(
                                {
                                    "event": "slice_complete",
                                    "slice_start": _date_yyyymmdd(window_start),
                                    "slice_end": _date_yyyymmdd(cursor_end),
                                    "slice_total": slice_total,
                                    "slice_next_start": slice_next_start,
                                }
                            ),
                            flush=True,
                        )
                        break

                    time.sleep(sleep_sec)

                # move to next (older) slice
                cursor_end = window_start - timedelta(days=1)
                slice_cursor_end = _date_yyyymmdd(cursor_end)
                slice_next_start = 0
                start = 0
                write_checkpoint("slice_advance")
                time.sleep(sleep_sec)

        else:
            # Original offset mode
            if total_available == 0:
                print(json.dumps({"event": "init_total_fetch", "query": query}), flush=True)
                first = fetch_feed(
                    query,
                    start=0,
                    page_size=1,
                    timeout=fetch_timeout,
                    max_retries=fetch_max_retries,
                    verbose=True,
                )
                total_available = parse_total(first)

            while start < total_available and pages_done_this_run < max_pages:
                data_bytes = dir_size_bytes(Path("data"))
                if data_bytes >= int(storage_budget_gb * stop_ratio * (1024**3)):
                    print(json.dumps({"event": "stop_storage_guard", "data_bytes": data_bytes}), flush=True)
                    break

                try:
                    xml = fetch_feed(
                        query,
                        start=start,
                        page_size=current_page_size,
                        timeout=fetch_timeout,
                        max_retries=fetch_max_retries,
                        verbose=True,
                    )
                except RuntimeError as e:
                    last_error = str(e)
                    consecutive_failures += 1
                    if current_page_size > min_page_size:
                        current_page_size = max(min_page_size, current_page_size // 2)
                        print(
                            json.dumps(
                                {
                                    "event": "page_size_reduce_on_error",
                                    "start": start,
                                    "new_page_size": current_page_size,
                                    "consecutive_failures": consecutive_failures,
                                    "reason": last_error,
                                }
                            ),
                            flush=True,
                        )
                        write_checkpoint("page_size_reduce_on_error")
                        if cooldown_on_error_sec > 0:
                            print(json.dumps({"event": "cooldown_on_error", "start": start, "sleep_sec": cooldown_on_error_sec}), flush=True)
                            time.sleep(cooldown_on_error_sec)
                        continue

                    min_page_failures += 1
                    print(
                        json.dumps(
                            {
                                "event": "min_page_retry_failed",
                                "start": start,
                                "page_size": current_page_size,
                                "min_page_failures": min_page_failures,
                                "max_min_page_failures": max_min_page_failures,
                                "reason": last_error,
                            }
                        ),
                        flush=True,
                    )
                    write_checkpoint("min_page_retry_failed")
                    if cooldown_on_error_sec > 0:
                        print(json.dumps({"event": "cooldown_on_error", "start": start, "sleep_sec": cooldown_on_error_sec}), flush=True)
                        time.sleep(cooldown_on_error_sec)
                    if min_page_failures < max_min_page_failures:
                        continue
                    print(json.dumps({"event": "fatal_fetch_error", "start": start, "reason": last_error}), flush=True)
                    write_checkpoint("fatal_fetch_error")
                    break

                entries = parse_entries(xml)
                consecutive_failures = 0
                min_page_failures = 0
                if not entries:
                    break

                written = 0
                dupes = 0
                for entry in entries:
                    wid = entry.get("work_id", "")
                    if not wid or wid in seen_ids:
                        dupes += 1
                        continue
                    seen_ids.add(wid)
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    kept += 1
                    written += 1

                pages_done += 1
                pages_done_this_run += 1
                start += len(entries)

                elapsed = max(1e-6, time.time() - run_started)
                rate = kept / elapsed
                remaining = max(0, total_available - start)
                eta_min = (remaining / rate) / 60.0 if rate > 0 else None
                pct = (start / total_available * 100.0) if total_available > 0 else 0.0
                print(
                    json.dumps(
                        {
                            "event": "progress",
                            "mode": "offset",
                            "next_start": start,
                            "total_available": total_available,
                            "progress_pct": round(pct, 3),
                            "written": written,
                            "dupes": dupes,
                            "kept": kept,
                            "pages_done": pages_done,
                            "pages_done_this_run": pages_done_this_run,
                            "page_size_requested": current_page_size,
                            "entries_returned": len(entries),
                            "rate_records_per_sec": round(rate, 3),
                            "eta_minutes": round(eta_min, 2) if eta_min is not None else None,
                        }
                    ),
                    flush=True,
                )

                if current_page_size < page_size and pages_done_this_run % 10 == 0:
                    current_page_size = min(page_size, current_page_size * 2)
                    print(json.dumps({"event": "page_size_restore", "start": start, "page_size": current_page_size}), flush=True)

                now = time.time()
                if pages_done % checkpoint_every == 0 or (now - last_checkpoint_ts) >= checkpoint_interval_sec:
                    write_checkpoint("periodic")

                time.sleep(sleep_sec)

    final = {
        "mode": mode,
        "query": query,
        "total_available": total_available,
        "next_start": start,
        "kept": kept,
        "pages_done": pages_done,
        "pages_done_this_run": pages_done_this_run,
        "current_page_size": current_page_size,
        "slice_days": slice_days,
        "slice_cursor_end": slice_cursor_end,
        "slice_next_start": slice_next_start,
        "output": str(out_path),
        "checkpoint": str(ck_path),
        "last_error": last_error,
    }
    ck_path.write_text(json.dumps(final, indent=2), encoding="utf-8")
    print(json.dumps(final), flush=True)


if __name__ == "__main__":
    main()
