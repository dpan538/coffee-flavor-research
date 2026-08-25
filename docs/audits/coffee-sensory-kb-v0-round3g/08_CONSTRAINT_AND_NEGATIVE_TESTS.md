# Constraint and negative-test audit

Round 3G registers 18 new constraint rules and executes 20 negative cases. The
suite rejects missing source families, mismatched hashes, mirror independence,
duplicate-origin family counting, one-family cross-source promotion, missing
locators/reviews, text intuition, below-threshold occurrence, false question
validation/information gain, literal-translation bilingual promotion,
calibration/new-range activation, canonical creation, co-occurrence-to-neighbour
inference, contradictory-evidence deletion, false PASS classification,
undocumented threshold revision and Round 3G model use.

`CONSTRAINT_TEST_PASS=true`; the exact database constraint names and SQLSTATEs
are asserted in `db/tests/round3g_negative.sql`.
