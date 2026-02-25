from pydantic import BaseModel, Field


class Citation(BaseModel):
    work_id: str
    passage_id: str | None = None


class Claim(BaseModel):
    text: str
    supporting_citations: list[Citation] = Field(default_factory=list)
    support_level: str = "direct"


class GroundedAnswer(BaseModel):
    answer_summary: str
    claims: list[Claim] = Field(default_factory=list)
    references: list[dict] = Field(default_factory=list)
    confidence: str = "insufficient_evidence"
    limitations: list[str] = Field(default_factory=list)
    query_refinements: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class QARequest(BaseModel):
    query: str
    mode: str = "brief"


class VerifyRequest(BaseModel):
    answer: GroundedAnswer


class VerifyResponse(BaseModel):
    ok: bool
    verified_claims: int
    total_claims: int
    invalid_claim_indices: list[int] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    coverage_ratio: float = 0.0
    suggested_confidence: str = "insufficient_evidence"
    must_abstain: bool = True
