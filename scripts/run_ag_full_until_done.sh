#!/usr/bin/env bash
set -u

cd "$(dirname "$0")/.." || exit 1
COMPOSE="docker compose -f deploy/docker-compose.selfhost.yml"
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/ag_full_runner.log"
STATE_FILE="$LOG_DIR/ag_full_state.env"

if [ -f "$STATE_FILE" ]; then
  # shellcheck disable=SC1090
  source "$STATE_FILE"
else
  CYCLE=0
fi

while true; do
  CYCLE=$((CYCLE+1))
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "[$ts] cycle=$CYCLE start" >> "$LOG_FILE"

  $COMPOSE run --rm -T \
    -e MATHFOUNDRY_ALL_AG_PAGE_SIZE=200 \
    -e MATHFOUNDRY_ALL_AG_MAX_PAGES=100 \
    -e MATHFOUNDRY_ALL_AG_SLEEP_SEC=1.5 \
    -e MATHFOUNDRY_ALL_AG_CHECKPOINT_EVERY=10 \
    -e MATHFOUNDRY_ALL_AG_STOP_RATIO=0.9 \
    worker python scripts/fetch_ag_all.py >> "$LOG_FILE" 2>&1
  rc=$?

  # Reindex every 4 cycles only (faster ingest throughput)
  if [ $((CYCLE % 4)) -eq 0 ]; then
    $COMPOSE run --rm -T worker python scripts/build_lexical_index.py >> "$LOG_FILE" 2>&1 || true
  fi

  done_flag=$(python3 - <<'PY'
import json
from pathlib import Path
ck = Path('data/topic/ag_all_checkpoint.json')
if not ck.exists():
    print('0')
else:
    d = json.loads(ck.read_text())
    total = int(d.get('total_available', 0) or 0)
    nxt = int(d.get('next_start', 0) or 0)
    print('1' if total > 0 and nxt >= total else '0')
PY
)

  echo "CYCLE=$CYCLE" > "$STATE_FILE"

  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  if [ "$done_flag" = "1" ]; then
    echo "[$ts] completed full math.AG ingest" >> "$LOG_FILE"
    $COMPOSE run --rm -T worker python scripts/build_lexical_index.py >> "$LOG_FILE" 2>&1 || true
    exit 0
  fi

  if [ "$rc" -ne 0 ]; then
    echo "[$ts] fetch cycle failed rc=$rc; sleeping 300s then retry" >> "$LOG_FILE"
    sleep 300
  else
    echo "[$ts] fetch cycle ok; sleeping 20s before next chunk" >> "$LOG_FILE"
    sleep 20
  fi
done
