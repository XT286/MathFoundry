# Lean Evaluation for MathFoundry

## Short answer
Lean is promising for long-term theorem-level rigor, but it is **not the right dependency for MVP**.

## Why Lean is valuable
- Formal semantics for theorems/proofs (where formalized)
- Strong verification guarantees inside formal libraries
- Potential future bridge from natural language claims to formal checks

## Why Lean should not block MVP
1. **Coverage gap:** most arXiv math papers are not formalized in Lean.
2. **Parsing gap:** mapping paper prose/LaTeX directly to Lean is a research problem.
3. **Complexity/cost:** adding Lean infra now slows the core objective (reliable citation-grounded QA).
4. **User value timing:** immediate value comes from grounded retrieval + citation verification.

## Recommended strategy
### Phase 0–1 (MVP, current)
- Do not require Lean in serving path.
- Focus on retrieval, grounding, and abstention correctness.

### Phase 2 (targeted pilot)
- Add optional Lean augmentation for selected domains where formal libraries are strong.
- Start with a narrow set of theorem families and explicit “formalization available” flags.

### Phase 3 (research track)
- Explore claim-to-formal-statement linking and partial formal validation workflows.

## Decision
Use Lean as an **optional advanced module later**, not a core MVP dependency.
