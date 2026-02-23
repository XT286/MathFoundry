# RFC-0006: Web UX and “Ask MathFoundry” Interaction Model

- **Status:** Draft
- **Author:** Javis
- **Created:** 2026-02-22
- **Target Version:** MVP (v0.1)
- **Related:**
  - `docs/PRD.md`
  - `docs/RFC-0001-citation-grounded-qa-architecture.md`
  - `docs/RFC-0003-retrieval-and-reranking-strategy.md`
  - `docs/RFC-0004-grounded-answer-generation-and-citation-verification.md`
  - `docs/RFC-0005-hosted-deployment-and-cost-model.md`

---

## 1. Summary

This RFC defines the MVP web experience for mathematicians:

- a single, low-friction **Ask** workflow,
- citation-grounded answers by default,
- transparent evidence/provenance UI,
- abstention/refinement UX when confidence is low.

Goal: make MathFoundry feel like a trustworthy math research copilot, not a generic chatbot.

---

## 2. Motivation

Most researchers won’t adopt tools that require setup complexity or opaque outputs.

Adoption requires:

1. immediate utility in < 60 seconds,
2. clear answer + evidence presentation,
3. easy export into existing workflows (BibTeX/links/notes),
4. obvious trust signals (confidence, citations, limits).

---

## 3. Goals

1. Deliver a web-first UX requiring zero local setup.
2. Make “ask question -> get grounded answer” the primary action.
3. Surface citation evidence without cluttering the main response.
4. Support common research intents (lookup/survey/compare/prereq).

## Non-goals (MVP)

- Full collaborative workspace features.
- Personalized recommendation feed.
- Native mobile apps.

---

## 4. User personas and key jobs

1. **Graduate student**
   - Job: get starter references + prerequisites quickly.
2. **Active researcher**
   - Job: validate if key papers are missing in current reading list.
3. **Professor/advisor**
   - Job: gather canonical references + compare approaches for seminars.

Primary job-to-be-done:
> “Answer my math question with references I can trust and inspect quickly.”

---

## 5. Core interaction model

## 5.1 Primary entry point

Single input box with prompt:

> “Ask a math literature question…”

Examples shown inline:
- “Foundational references for Ricci flow singularities”
- “Compare approaches to proving theorem X”
- “What should I read before paper Y?”

## 5.2 Response layout

Each answer page/card contains:

1. **Answer summary** (top)
2. **Confidence badge** (`High / Medium / Low / Insufficient evidence`)
3. **Key claims** with inline citation anchors `[1], [2]`
4. **References panel** (title/authors/year/source links)
5. **Evidence drawer** (source passages for each claim)
6. **Limitations and uncertainty notes**
7. **Refine query suggestions**

## 5.3 Interaction principles

- Default to concise answers, expandable details.
- Never hide uncertainty.
- Keep provenance one click away.
- Preserve a session history of prior queries.

---

## 6. Key screens (MVP)

## 6.1 Ask screen (main)

Components:
- question input,
- optional filters (branch/date/source),
- ask button,
- recent queries.

## 6.2 Answer screen

Components:
- summary + confidence,
- claim list with citations,
- references list,
- evidence panel mapping claim -> supporting passage,
- actions:
  - copy answer,
  - export BibTeX,
  - open source link,
  - mark “helpful / not helpful”.

## 6.3 Paper detail screen

Components:
- bibliographic metadata,
- abstract,
- subject tags,
- citation neighbors (cited-by / references),
- highlighted passages used in answers.

---

## 7. Trust UX requirements

1. **No citation, no highlighted claim** in UI.
2. Confidence badge always visible.
3. Insufficient evidence answers must have explicit abstention message.
4. Every reference links to canonical source page.
5. Evidence drawer displays passage text and section context where available.

---

## 8. Error and abstention UX

When system abstains:

- show “Insufficient evidence for a reliable answer.”
- show top related references found,
- suggest 2–4 refined queries,
- suggest filter changes (e.g., subfield/date).

For system errors (timeouts/index issues):

- show friendly retry message,
- preserve query draft,
- offer fallback “show top references only.”

---

## 9. Accessibility and usability

MVP requirements:

- keyboard-first navigation,
- readable typography for long technical text,
- dark mode support,
- semantic headings/ARIA for major components,
- screen-width responsive layout (desktop-first, mobile-usable).

---

## 10. Information architecture and state

## 10.1 Session model

A query session stores:
- user query,
- retrieval metadata,
- grounded answer object,
- feedback signal.

## 10.2 URL strategy

- shareable answer URLs with stable IDs,
- paper detail pages by canonical work ID,
- query params for filters.

---

## 11. API contracts consumed by web app

Required endpoints:

- `POST /qa`
- `POST /search`
- `GET /work/{id}`
- `POST /feedback` (helpful/not helpful + reason)

Web app must render directly from `GroundedAnswer` schema from RFC-0004.

---

## 12. MVP metrics (product + UX)

Adoption:
- time-to-first-answer,
- weekly active users,
- repeat query rate.

Trust/quality:
- helpful vote rate,
- “citation inspected” interaction rate,
- abstention acceptance rate (low negative feedback on abstentions),
- query reformulation success rate.

Usability:
- median clicks to export references,
- drop-off before first query.

---

## 13. Rollout plan

1. Build ask + answer + references MVP screens.
2. Integrate grounded answer contract.
3. Add evidence drawer and confidence badge.
4. Add export and feedback actions.
5. Run pilot with 10–20 mathematicians and iterate.

---

## 14. Acceptance criteria

RFC-0006 is implemented for MVP when:

1. user can ask a query and receive grounded answer in one flow,
2. every displayed claim has inspectable citation evidence,
3. abstention/refinement path is implemented,
4. BibTeX/export and source-link actions work,
5. feedback capture is active,
6. pilot users can complete core tasks without onboarding calls.

---

## 15. Alternatives considered

1. **Reference-first UI (list-only)**
   - Rejected: weak value vs existing search tools.

2. **Chat-only UI with hidden evidence**
   - Rejected: low trust and poor inspectability.

3. **Complex dashboard-first UX**
   - Rejected for MVP: too much friction.

Chosen: ask-first, answer-plus-evidence workflow.

---

## 16. Open questions

1. Should evidence drawer open by default for low-confidence answers?
2. What is best default answer length for researcher preference?
3. Should user-selectable answer modes (`concise`, `deep`) be MVP or phase 2?
4. Should anonymous mode be allowed in public beta?

---

## 17. Decision record

Pending maintainer approval.

On acceptance, RFC-0006 becomes the normative web UX contract for MVP.
