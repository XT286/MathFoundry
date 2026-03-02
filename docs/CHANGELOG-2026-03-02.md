# Changelog — 2026-03-02

## Phase A: OpenAI Integration (Complete)

### Core Changes
- **`mathfoundry/grounding.py`** — Replaced scaffold `answer_with_grounding()` with real OpenAI Responses API integration:
  - Sends top-N retrieved passages as context to `gpt-4.1`
  - Parses structured JSON response into `GroundedAnswer` with proper claims, citations, and confidence
  - Graceful fallback to scaffold mode if `OPENAI_API_KEY` is not set or API call fails
  - Correct parsing of Responses API format (`output[].content[].text`)

- **`mathfoundry/config.py`** — Added `openai_api_key` and `openai_model` fields (read from `OPENAI_API_KEY` and `MATHFOUNDRY_OPENAI_MODEL` env vars)

- **`mathfoundry/app.py`** — Health endpoint now reports `openai_model` and `openai_configured` status

- **`.env.example`** — New file documenting all supported environment variables (API key placeholder, not real key)

### Eval Script Fixes
- **`eval/scripts/run_s0_openai.py`** — Fixed OpenAI Responses API parsing (was using non-existent `output_text` top-level field)
- **`eval/scripts/run_s2_openai_rag.py`** — Same fix

## Phase B: Codebase Cleanup & Refactoring

### New Shared Modules (DRY)
- **`mathfoundry/arxiv.py`** — Consolidated ArXiv API functions (`fetch_feed`, `parse_entries`, `parse_total`, `dir_size_bytes`) previously duplicated across 4 files
- **`mathfoundry/io_utils.py`** — Consolidated `load_jsonl`/`write_jsonl` helpers previously copy-pasted across 4 eval scripts

### Refactored Scripts
- **`scripts/fetch_ag_all.py`** — Now imports from `mathfoundry.arxiv` (~100 lines removed)
- **`scripts/fetch_ag_focus_10k.py`** — Same treatment (~108 lines removed)
- **`scripts/fetch_arxiv_slice.py`** — Uses shared `fetch_feed` (gains retry logic it previously lacked)
- **`scripts/ingest_arxiv_math_ag.py`** — Uses shared `fetch_feed`
- **`scripts/worker_ingest_loop.py`** — Uses `sys.executable` instead of hardcoded `"python"` for subprocess calls
- **`mathfoundry/indexing.py`** — `parse_arxiv_atom` delegates to shared parser
- **All 4 eval scripts** — Use `mathfoundry.io_utils` for JSONL I/O

### Dead Code Removed
- **`QARequest.mode`** field — accepted but never used anywhere
- **Demo fallback in `retrieval.py`** — hardcoded fake result for keyword matches; misleading now that real data exists

### Test Updates
- `test_search_returns_demo_for_ag_terms` → `test_search_returns_results_or_empty` (adapted to removal of demo fallback)

### Net Result
- **15 files changed**, ~255 lines of redundant code eliminated
- All 9 tests pass

## Server vs Local Relationship
- Both are clones of `github.com/XT286/MathFoundry`
- Local was 7 commits ahead of server before this sync
- Server had uncommitted modifications (Dockerfile, docker-compose, web.py) that matched earlier local commits
- Server has more ingested data: 11,600 topic JSONL lines vs ~6,000 local; 3,052 indexed papers vs 3,000 local
- Server has stale duplicate files in project root (`web.py`, `preset_ag_v1.jsonl`, `run_baseline_compare.py`)
