from __future__ import annotations

import re

AG_SUBAREA_KEYWORDS: dict[str, list[str]] = {
    "birational_geometry_mmp": ["birational", "minimal model", "mmp", "log canonical", "klt", "flip", "fano"],
    "moduli_and_stacks": ["moduli", "stack", "stable map", "hilbert scheme", "quot scheme"],
    "derived_and_homological_ag": ["derived", "dg", "triangulated", "derived category", "t-structure", "stability condition"],
    "arithmetic_geometry": ["diophantine", "number field", "arithmetic", "height", "l-function", "galois representation"],
    "cohomology_and_sheaves": ["etale", "étale", "cohomology", "sheaf", "de rham", "crystalline", "perverse"],
    "singularities": ["singularity", "resolution", "multiplier ideal", "log resolution"],
    "enumerative_and_intersection": ["gromov-witten", "enumerative", "intersection", "donaldson-thomas", "curve counting"],
    "abelian_k3_calabi_yau": ["abelian variety", "k3", "calabi-yau", "hyperkahler", "holomorphic symplectic"],
    "toric_and_tropical": ["toric", "fan", "polytope", "tropical"],
    "geometric_invariant_theory": ["git", "geometric invariant theory", "stability", "quotient"],
}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def detect_ag_subareas(text: str, max_tags: int = 3) -> list[str]:
    t = _normalize(text)
    scored: list[tuple[str, int]] = []
    for tag, kws in AG_SUBAREA_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in t)
        if score > 0:
            scored.append((tag, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in scored[:max_tags]]
