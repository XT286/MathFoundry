from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


_DEF_PRESETS = [
    "What is the derived category of coherent sheaves, and why is it useful in algebraic geometry?",
    "Foundational references for étale cohomology aimed at algebraic geometers.",
    "Key references around the Weil conjectures proof strategy and later expositions.",
    "Important papers/books on minimal model program in algebraic geometry.",
    "References for algebraic stacks with emphasis on deformation theory.",
    "References connecting homological mirror symmetry and algebraic geometry.",
]


def _load_presets() -> list[str]:
    root = Path(__file__).resolve().parents[1]
    path = root / "queries" / "preset_ag_v1.jsonl"
    if not path.exists():
        return _DEF_PRESETS

    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        q = str(row.get("query", "")).strip()
        if q:
            out.append(q)

    return out or _DEF_PRESETS


@router.get("/presets")
def presets() -> dict:
    vals = _load_presets()
    return {"count": len(vals), "queries": vals}


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
    .wrap { max-width: 1080px; margin: 0 auto; }
    h1 { margin-bottom: 8px; }
    .muted { color: #a5b4d4; }
    textarea,input,button,select { font: inherit; }
    textarea { width: 100%; min-height: 110px; border-radius: 10px; border: 1px solid #2a355a; background: #101a33; color: #eaf0ff; padding: 12px; }
    .row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    button { border: 0; border-radius: 10px; padding: 10px 14px; cursor: pointer; background: #5b8cff; color: white; }
    button.secondary { background: #243154; }
    .card { margin-top: 16px; border: 1px solid #2a355a; border-radius: 12px; padding: 14px; background: #101a33; }
    .badge { display: inline-block; border-radius: 999px; padding: 4px 10px; background: #243154; color: #c9d7ff; margin-left: 8px; font-size: 12px; }
    .small { font-size: 13px; color: #a5b4d4; }
    ul { margin-top: 8px; }
    code { background: #0b1329; border: 1px solid #253254; padding: 1px 6px; border-radius: 6px; }
    select { background: #0b1329; color: #eaf0ff; border: 1px solid #253254; border-radius: 10px; padding: 8px; min-width: 520px; max-width: 100%; }
  </style>
</head>
<body>
<div class=\"wrap\">
  <h1>MathFoundry <span class=\"badge\">Ask (MVP)</span></h1>
  <div class=\"muted\">Ask a math literature question. The app returns grounded answers with citations and verification.</div>

  <div class=\"card\">
    <label for=\"preset\" class=\"small\">Preset query list</label>
    <div class=\"row\">
      <select id=\"preset\"><option>Loading presets...</option></select>
      <button id=\"loadPresetBtn\" class=\"secondary\">Load selected</button>
      <button id=\"randomPresetBtn\" class=\"secondary\">Random</button>
    </div>

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
const preset = document.getElementById('preset');
let presetQueries = [];

function esc(s){return (s||'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));}

async function loadPresets(){
  try {
    const r = await fetch('/presets');
    const j = await r.json();
    presetQueries = j.queries || [];
    preset.innerHTML = '';
    for (const query of presetQueries){
      const opt = document.createElement('option');
      opt.value = query;
      opt.textContent = query;
      preset.appendChild(opt);
    }
    if (!presetQueries.length){
      preset.innerHTML = '<option>No presets found</option>';
    }
  } catch (e) {
    preset.innerHTML = '<option>Failed to load presets</option>';
  }
}

function loadSelectedPreset(){
  const selected = preset.value || '';
  if (selected) q.value = selected;
}

function loadRandomPreset(){
  if (!presetQueries.length) return;
  const idx = Math.floor(Math.random() * presetQueries.length);
  q.value = presetQueries[idx];
}

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
document.getElementById('loadPresetBtn').addEventListener('click', loadSelectedPreset);
document.getElementById('randomPresetBtn').addEventListener('click', loadRandomPreset);

loadPresets();
</script>
</body>
</html>"""