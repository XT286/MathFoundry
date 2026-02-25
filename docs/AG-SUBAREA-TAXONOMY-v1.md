# AG Subarea Taxonomy v1

This taxonomy is used for lightweight tagging during ingestion and for retrieval boosts.

## Tags
- birational_geometry_mmp
- moduli_and_stacks
- derived_and_homological_ag
- arithmetic_geometry
- cohomology_and_sheaves
- singularities
- enumerative_and_intersection
- abelian_k3_calabi_yau
- toric_and_tropical
- geometric_invariant_theory

## Usage in system
1. Detect tags from title + abstract keyword matches.
2. Store tags on each indexed paper (`ag_subareas`).
3. At query time, detect query tags and apply small score boost for overlap.

## Important note
These tags are retrieval aids, not correctness guarantees. They help ranking focus but do not replace citation-grounded verification.
