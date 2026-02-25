from .models import Claim, Citation, GroundedAnswer, VerifyResponse

_ALLOWED_SUPPORT_LEVELS = {"direct", "indirect"}
_ALLOWED_CONFIDENCE = {"high", "medium", "low", "insufficient_evidence"}


def answer_with_grounding(query: str, candidates: list[dict]) -> GroundedAnswer:
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

    top = candidates[0]
    claim = Claim(
        text=f"A likely relevant starting reference is '{top['title']}'.",
        supporting_citations=[Citation(work_id=top["work_id"])],
        support_level="direct",
    )
    return GroundedAnswer(
        answer_summary="Here is a citation-grounded starting point from the indexed algebraic-geometry-focused corpus.",
        claims=[claim],
        references=[top],
        confidence="low",
        limitations=["MVP scaffold answer; full passage-level verification not yet enabled."],
        query_refinements=["Ask for theorem-level comparison once ingestion and passage indexing expands."],
    )


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
