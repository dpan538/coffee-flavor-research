# Candidate and context state

`PRODUCT_CONCEPT_CANDIDATE.tsv` contains 20 canonical concepts whose English
and Simplified-Chinese labels already exist in the public pilot. Each row keeps
direct assertion, effective-record, source-family, governed normalization,
governed semantic, exploratory relation, structured contrast, rights, review,
redundancy, uncertainty, score-component, explanation, and lineage fields.

Support is log-bounded before weighting so one large source family cannot win
solely by volume. Weights are hand-declared sensitivity targets, not learned or
optimal coefficients. Review-required relations are visible but contribute no
independent primary admission.

`PRODUCT_CONTEXT_PRIOR.tsv` contains 1,120 rows (20 candidates × 56 cells).
Only exact Honey and Caramel rows receive bounded C0 adjustments (±0.25) from
within-study Vezzulli preparation aggregates. C1 contributes exactly zero in
every row because reviewed seven-level mappings remain zero. Missing evidence
also contributes zero.
