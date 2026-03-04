"""Citation-grounded answer generation and verification using OpenAI."""

from __future__ import annotations

import json
import logging
import re

import httpx

from .config import CONFIG
from .models import Claim, Citation, GroundedAnswer, VerifyResponse

logger = logging.getLogger(__name__)

_ALLOWED_SUPPORT_LEVELS = {"direct", "indirect"}
_ALLOWED_CONFIDENCE = {"high", "medium", "low", "insufficient_evidence"}

# ---------------------------------------------------------------------------
# OpenAI-powered grounded answer generation
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are MathFoundry, a citation-grounded math-literature research assistant.
Your job: answer the user's query using ONLY the provided reference passages.

Rules:
1. Every factual claim MUST cite at least one reference by its work_id.
2. If the references are insufficient, say so and set confidence to "insufficient_evidence".
3. Do NOT fabricate citations or invent paper titles.
4. Respond in the exact JSON schema below (no markdown, no extra keys).

JSON schema:
{
  "answer_summary": "...",
  "claims": [
    {
      "text": "One factual claim sentence.",
      "supporting_citations": [{"work_id": "arxiv:XXXX.XXXXX"}],
      "support_level": "direct"   // or "indirect"
    }
  ],
  "confidence": "high" | "medium" | "low" | "insufficient_evidence",
  "limitations": ["..."],
  "query_refinements": ["..."]
}
"""


def _build_context(candidates: list[dict], max_refs: int = 8) -> str:
    """Format retrieved candidates into a numbered reference block."""
    lines = []
    for i, c in enumerate(candidates[:max_refs], start=1):
        wid = c.get("work_id", "unknown")
        title = c.get("title", "")
        summary = (c.get("summary", "") or "")[:600]
        lines.append(f"[{i}] work_id={wid}\n    title: {title}\n    summary: {summary}")
    return "\n\n".join(lines)


def _extract_first_json_object(text: str) -> str:
    """Extract the first top-level JSON object from text."""
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object start found in model output")

    in_string = False
    escaped = False
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    raise ValueError("Unbalanced JSON object in model output")


def _load_model_json(raw: str) -> dict:
    """Parse model JSON robustly; repair invalid backslash escapes when needed."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Sometimes model adds prose around JSON; extract object region.
        obj_text = _extract_first_json_object(text)
        try:
            return json.loads(obj_text)
        except json.JSONDecodeError:
            # Common issue: invalid backslash escapes from LaTeX fragments.
            repaired = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", obj_text)
            return json.loads(repaired)


def _call_openai(query: str, context: str) -> dict:
    """Call OpenAI Responses API and parse the JSON output."""
    user_msg = f"Query: {query}\n\nReferences:\n{context}"

    with httpx.Client(
        headers={
            "Authorization": f"Bearer {CONFIG.openai_api_key}",
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0),
    ) as client:
        r = client.post(
            "https://api.openai.com/v1/responses",
            json={
                "model": CONFIG.openai_model,
                "instructions": _SYSTEM_PROMPT,
                "input": user_msg,
            },
        )
        r.raise_for_status()
        data = r.json()

    # Extract text from Responses API structure:
    # output -> [message] -> content -> [output_text] -> text
    raw = ""
    for msg in data.get("output", []):
        for block in msg.get("content", []):
            if block.get("type") == "output_text":
                raw = block.get("text", "")
                break
        if raw:
            break

    return _load_model_json(raw)


def answer_with_grounding(query: str, candidates: list[dict]) -> GroundedAnswer:
    """Generate a citation-grounded answer for *query* given retrieved *candidates*."""

    # No candidates → abstain immediately
    if not candidates:
        return GroundedAnswer(
            answer_summary="Insufficient evidence to answer reliably from current indexed corpus.",
            confidence="insufficient_evidence",
            limitations=["No relevant indexed candidates were found."],
            query_refinements=[
                "Add a specific theorem/object name (e.g., Picard group, étale cohomology).",
                "Narrow to algebraic geometry subtopic and include timeframe.",
            ],
        )

    # No API key → fall back to scaffold answer
    if not CONFIG.openai_api_key:
        top = candidates[0]
        claim = Claim(
            text=f"A likely relevant starting reference is '{top['title']}'.",
            supporting_citations=[Citation(work_id=top["work_id"])],
            support_level="direct",
        )
        return GroundedAnswer(
            answer_summary="Here is a citation-grounded starting point from the indexed corpus. (OpenAI key not configured — scaffold mode.)",
            claims=[claim],
            references=[top],
            confidence="low",
            limitations=["Scaffold answer; set OPENAI_API_KEY for full LLM-powered grounding."],
        )

    # Full LLM-grounded answer
    context = _build_context(candidates)
    ref_lookup = {c["work_id"]: c for c in candidates}

    try:
        parsed = _call_openai(query, context)
    except Exception as exc:
        logger.warning("OpenAI call failed: %s — falling back to scaffold", exc)
        top = candidates[0]
        claim = Claim(
            text=f"A likely relevant starting reference is '{top['title']}'.",
            supporting_citations=[Citation(work_id=top["work_id"])],
            support_level="direct",
        )
        return GroundedAnswer(
            answer_summary=f"OpenAI call failed ({type(exc).__name__}); showing top retrieval result instead.",
            claims=[claim],
            references=[top],
            confidence="low",
            limitations=[f"LLM call failed: {exc}"],
        )

    # Parse claims
    claims: list[Claim] = []
    for raw_claim in parsed.get("claims", []):
        cits = [
            Citation(work_id=c.get("work_id", ""), passage_id=c.get("passage_id"))
            for c in raw_claim.get("supporting_citations", [])
        ]
        claims.append(
            Claim(
                text=raw_claim.get("text", ""),
                supporting_citations=cits,
                support_level=raw_claim.get("support_level", "direct"),
            )
        )

    # Collect cited references
    cited_ids = set()
    for c in claims:
        for cit in c.supporting_citations:
            cited_ids.add(cit.work_id)

    references = [ref_lookup[wid] for wid in cited_ids if wid in ref_lookup]
    # Also include top candidates even if not explicitly cited
    for c in candidates[:5]:
        if c["work_id"] not in {r["work_id"] for r in references}:
            references.append(c)

    confidence = parsed.get("confidence", "low")
    if confidence not in _ALLOWED_CONFIDENCE:
        confidence = "low"

    return GroundedAnswer(
        answer_summary=parsed.get("answer_summary", ""),
        claims=claims,
        references=references,
        confidence=confidence,
        limitations=parsed.get("limitations", []),
        query_refinements=parsed.get("query_refinements", []),
    )


# ---------------------------------------------------------------------------
# Verification (unchanged logic)
# ---------------------------------------------------------------------------


def _confidence_from_ratio(ratio: float) -> str:
    if ratio >= 0.9:
        return "high"
    if ratio >= 0.75:
        return "medium"
    if ratio >= 0.5:
        return "low"
    return "insufficient_evidence"


def verify_grounded_answer(answer: GroundedAnswer) -> VerifyResponse:
    invalid: list[int] = []
    reasons: list[str] = []

    reference_ids = {str(r.get("work_id", "")).strip() for r in answer.references if isinstance(r, dict)}
    if answer.claims and not reference_ids:
        reasons.append("claims exist but references list is empty")

    if answer.confidence not in _ALLOWED_CONFIDENCE:
        reasons.append(f"confidence '{answer.confidence}' is invalid")

    for i, c in enumerate(answer.claims):
        claim_invalid = False

        if c.support_level not in _ALLOWED_SUPPORT_LEVELS:
            claim_invalid = True
            reasons.append(f"claim[{i}] has invalid support_level '{c.support_level}'")

        if not c.supporting_citations:
            claim_invalid = True
            reasons.append(f"claim[{i}] has no supporting citations")
        else:
            seen = set()
            for cit in c.supporting_citations:
                wid = (cit.work_id or "").strip()
                if not wid:
                    claim_invalid = True
                    reasons.append(f"claim[{i}] has empty citation work_id")
                    continue
                if wid in seen:
                    reasons.append(f"claim[{i}] contains duplicate citation '{wid}'")
                seen.add(wid)

                if reference_ids and wid not in reference_ids:
                    claim_invalid = True
                    reasons.append(f"claim[{i}] cites work_id '{wid}' not present in references[]")

        if claim_invalid:
            invalid.append(i)

    total = len(answer.claims)
    verified = max(0, total - len(set(invalid)))
    ratio = float(verified / total) if total > 0 else 0.0
    suggested_confidence = _confidence_from_ratio(ratio)
    must_abstain = suggested_confidence == "insufficient_evidence"

    # confidence consistency warning
    if total > 0 and answer.confidence in _ALLOWED_CONFIDENCE:
        if answer.confidence in {"high", "medium"} and ratio < 0.75:
            reasons.append("declared confidence appears overstated for verification ratio")

    ok = len(set(invalid)) == 0 and not must_abstain
    return VerifyResponse(
        ok=ok,
        verified_claims=verified,
        total_claims=total,
        invalid_claim_indices=sorted(set(invalid)),
        reasons=reasons,
        coverage_ratio=round(ratio, 4),
        suggested_confidence=suggested_confidence,
        must_abstain=must_abstain,
    )
