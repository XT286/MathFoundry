from .models import Claim, Citation, GroundedAnswer


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
