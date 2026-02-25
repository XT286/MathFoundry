from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>MathFoundry</title>
  <style>
    body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; background: #0b1020; color: #eaf0ff; }
    .wrap { max-width: 960px; margin: 0 auto; }
    h1 { margin-bottom: 8px; }
    .muted { color: #a5b4d4; }
    textarea,input,button { font: inherit; }
    textarea { width: 100%; min-height: 110px; border-radius: 10px; border: 1px solid #2a355a; background: #101a33; color: #eaf0ff; padding: 12px; }
    .row { display: flex; gap: 8px; margin-top: 10px; }
    button { border: 0; border-radius: 10px; padding: 10px 14px; cursor: pointer; background: #5b8cff; color: white; }
    button.secondary { background: #243154; }
    .card { margin-top: 16px; border: 1px solid #2a355a; border-radius: 12px; padding: 14px; background: #101a33; }
    .badge { display: inline-block; border-radius: 999px; padding: 4px 10px; background: #243154; color: #c9d7ff; margin-left: 8px; font-size: 12px; }
    .small { font-size: 13px; color: #a5b4d4; }
    ul { margin-top: 8px; }
    code { background: #0b1329; border: 1px solid #253254; padding: 1px 6px; border-radius: 6px; }
  </style>
</head>
<body>
<div class=\"wrap\">
  <h1>MathFoundry <span class=\"badge\">Ask (MVP)</span></h1>
  <div class=\"muted\">Ask a math literature question. The app returns grounded answers with citations and verification.</div>

  <div class=\"card\">
    <label for=\"q\" class=\"small\">Question</label>
    <textarea id=\"q\" placeholder=\"Example: Foundational references for étale cohomology in algebraic geometry\"></textarea>
    <div class=\"row\">
      <button id=\"askBtn\">Ask</button>
      <button id=\"searchBtn\" class=\"secondary\">Search only</button>
    </div>
  </div>

  <div id=\"answer\" class=\"card\" style=\"display:none\"></div>
  <div id=\"search\" class=\"card\" style=\"display:none\"></div>
</div>

<script>
const q = document.getElementById('q');
const answer = document.getElementById('answer');
const searchBox = document.getElementById('search');

function esc(s){return (s||'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}

async function ask(){
  const query = q.value.trim();
  if(!query) return;
  answer.style.display='block';
  answer.innerHTML='Running...';
  const r = await fetch('/qa',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({query})});
  const j = await r.json();

  const claims = (j.claims||[]).map((c,idx)=>`<li><b>Claim ${idx+1}:</b> ${esc(c.text)}<br><span class=\"small\">Citations: ${(c.supporting_citations||[]).map(x=>`<code>${esc(x.work_id)}</code>`).join(' ')||'none'}</span></li>`).join('');
  const refs = (j.references||[]).map((x,idx)=>`<li>[${idx+1}] ${esc(x.title||x.work_id||'unknown')} <span class=\"small\">${esc(x.work_id||'')}</span></li>`).join('');
  const verify = j.verification || {};

  answer.innerHTML = `
    <h3>Answer <span class=\"badge\">${esc(j.confidence||'unknown')}</span></h3>
    <p>${esc(j.answer_summary||'')}</p>
    <div class=\"small\">Verification: ok=${verify.ok} | coverage=${verify.coverage_ratio} | suggested=${verify.suggested_confidence} | abstain=${verify.must_abstain}</div>
    <h4>Claims</h4>
    <ul>${claims || '<li>No claims</li>'}</ul>
    <h4>References</h4>
    <ul>${refs || '<li>No references</li>'}</ul>
    <h4>Limitations</h4>
    <ul>${(j.limitations||[]).map(x=>`<li>${esc(x)}</li>`).join('') || '<li>None</li>'}</ul>
  `;
}

async function runSearch(){
  const query = q.value.trim();
  if(!query) return;
  searchBox.style.display='block';
  searchBox.innerHTML='Searching...';
  const r = await fetch('/search',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({query,limit:10})});
  const j = await r.json();
  const rows = (j.results||[]).map((x,idx)=>`<li>[${idx+1}] ${esc(x.title)} <span class=\"small\">${esc(x.work_id)} | score=${x.score} | block=${esc(x.top_block_type||'n/a')} | density=${x.math_density ?? 'n/a'}</span></li>`).join('');
  searchBox.innerHTML = `<h3>Search results (${j.count||0})</h3><ul>${rows || '<li>No results</li>'}</ul>`;
}

document.getElementById('askBtn').addEventListener('click', ask);
document.getElementById('searchBtn').addEventListener('click', runSearch);
</script>
</body>
</html>"""
