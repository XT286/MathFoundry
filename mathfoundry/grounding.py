from .models import Claim, Citation, GroundedAnswer, VerifyResponse


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


def verify_grounded_answer(answer: GroundedAnswer) -> VerifyResponse:
    invalid: list[int] = []
    reasons: list[str] = []

    for i, c in enumerate(answer.claims):
        if not c.supporting_citations:
            invalid.append(i)
            reasons.append(f"claim[{i}] has no supporting citations")
            continue
        for cit in c.supporting_citations:
            if not cit.work_id:
                invalid.append(i)
                reasons.append(f"claim[{i}] has invalid citation work_id")
                break

    total = len(answer.claims)
    verified = total - len(set(invalid))
    ok = len(invalid) == 0
    return VerifyResponse(
        ok=ok,
        verified_claims=max(0, verified),
        total_claims=total,
        invalid_claim_indices=sorted(set(invalid)),
        reasons=reasons,
    )
