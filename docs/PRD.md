# PRD — MathFoundry Agent (v0.1)

## 1) Problem Statement
Mathematicians using generic LLM tools frequently get:
- incorrect paper recommendations,
- weak understanding of theorem statements/assumptions,
- shallow summaries that miss proof ideas/examples,
- hallucinated citations.

This creates low trust and wasted research time.

## 2) Product Goal
Build an open-source system that ingests foundational math literature (starting with arXiv) and answers mathematicians’ queries with highly accurate, citation-grounded results.

## 3) Target Users
- PhD students and postdocs
- Faculty/researchers
- Advanced independent scholars

## 4) Core Value Proposition
For any math query, return:
1. the most relevant papers,
2. what each paper is actually about,
3. theorem-level/context-aware answers,
4. explicit citations and evidence.

## 5) Non-Negotiable Product Principles
- No citation, no claim
- Abstain over hallucinate
- Show evidence trails (paper section/snippet/context)
- Math-first retrieval (not generic web search behavior)

## 6) MVP Scope (Phase 1)
### In scope
- Ingest arXiv math corpus (metadata + available text)
- Hybrid search (keyword + semantic + citation graph hints)
- Query answering with citation-grounded outputs
- Paper cards: topic, key theorem focus, assumptions, methods, related works
- Web UI + API

### Out of scope
- Full proof verification
- Formal theorem proving integration
- Closed-paywalled full-text redistribution

## 7) User Stories
- As a researcher, I ask: "Best references for Ricci flow singularity formation," and get ranked papers with why each is relevant.
- As a student, I ask: "What are the prerequisites before reading paper X?" and get dependency-style references.
- As a mathematician, I ask theorem-level questions and receive cited evidence, not unsupported claims.

## 8) Functional Requirements
1. Corpus Ingestion
   - Scheduled arXiv sync
   - Versioned metadata and text extraction
2. Math-Aware Indexing
   - Formula-aware tokenization support (where feasible)
   - MSC-tag-aligned classification hooks
3. Retrieval
   - Hybrid retrieval (lexical + embedding + citation neighborhood)
   - Reranking tuned for math relevance
4. Answer Generation
   - Evidence-constrained generation
   - Claim-level citation mapping
   - Confidence/uncertainty labels
5. Explainability
   - Why this paper was selected
   - Which passages support each answer
6. Quality + Safety
   - Hallucination detection gates
   - Abstention path when evidence is weak

## 9) Success Metrics (MVP)
- Retrieval quality:
  - Recall@20 and nDCG@10 on curated math query set
- Answer quality:
  - Citation precision (claims backed by valid sources)
  - Expert-rated correctness score
- Trust signals:
  - Abstention correctness rate
  - User-reported "useful and reliable" score

## 10) Risks
- Misclassification across subfields
- Parsing issues for math-heavy text
- Citation graph incompleteness
- Hallucinations from generation layer

## 11) Mitigations
- Start with strict grounded mode + abstain
- Human-reviewed benchmark set by subfield
- Continuous error analysis loop
- Keep retrieval and answer generation separately measurable

## 12) Milestones (initial)
- M1: arXiv ingestion + searchable index baseline
- M2: hybrid retrieval + reranker + citation-aware outputs
- M3: grounded QA + expert evaluation loop
- M4: public MVP release

## 13) Open Questions
1. Should MVP focus first on 2–3 branches (e.g., geometry/topology/analysis) before all math?
2. What level of theorem-structure extraction is required in v1?
3. How much latency is acceptable for high-confidence answers?
4. What evaluation panel can we recruit early for expert scoring?
