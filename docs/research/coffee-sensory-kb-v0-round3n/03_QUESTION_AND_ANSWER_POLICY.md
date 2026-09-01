# Question and answer policy

Eight axes are represented. Seven divide the current candidate set and have at
least two supporting source families, so they may be exercised in the offline
simulator. The texture axis has research support but zero compatible concepts
in this flavor-only candidate package and is therefore ineligible.

All axes remain ineligible for production use because user comprehension and
information gain are `NOT_ESTIMABLE`. Existing bilingual wording is treated as
review material, not validation.

Offline selection orders eligible axes by declared separation score, coverage,
then stable axis ID. Each answered fixture records partition sizes, evidence
coverage, the hand-declared separation score, candidate counts before and
after, and the unsure/no-selection path in `question_trace_json`. Context-only
fixtures identify an eligible next Q1 but return no descriptor. Partial paths
may name a remaining Q2–Q4 axis; resolved or non-dividing paths stop early.
This is a transparent heuristic, not an empirically optimal adaptive policy.

Every option-to-candidate relation is typed as `supports`,
`weakly_supports`, `contradicts`, `weakly_contradicts`, `neutral`, `unknown`,
or `insufficient_evidence`. Unselected and unrelated candidates are neutral.
Only an explicit `none` option can provide weak structured contradiction;
ordinary non-mention never does. Unsure changes no evidence.
