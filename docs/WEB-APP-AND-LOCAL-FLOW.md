# Web App + Local End-to-End Flow

## Run web app locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn mathfoundry.app:app --reload
```

Open:
- http://localhost:8000/

## Pull a small arXiv slice (math.AG)
This pulls several recent pages and stores XML under `data/raw/`.
```bash
python scripts/fetch_arxiv_slice.py
```

## Build lexical index
```bash
python scripts/build_lexical_index.py
```

## Test end-to-end API flow quickly
```bash
python - <<'PY'
from fastapi.testclient import TestClient
from mathfoundry.app import app

c = TestClient(app)

print('health', c.get('/health').json())
print('search', c.post('/search', json={'query':'etale cohomology algebraic geometry', 'limit':5}).json()['count'])
qa = c.post('/qa', json={'query':'foundational references for etale cohomology'}).json()
print('qa confidence', qa.get('confidence'))
print('qa verify', qa.get('verification',{}))
PY
```

## Notes
- This is local smoke validation before server deployment.
- Server-side deployment can reuse the same scripts and docker-compose stack.

## Latest local smoke result (reference)
- Slice fetch: ~4.6 MB saved across 6 files (`math.AG`)
- Lexical index build: ~3000 rows indexed
- API flow: health OK, search returns results, QA returns grounded output with verification
