# Negative tests

`db/tests/round3h_negative.sql` contains 22 adversarial tests. They reject
undeclared source families, missing rights or hashes, unsafe public exports,
invalid feature semantics, incompatible pooling, missing grouping keys,
unsupported membership promotion, threshold revision, false readiness,
model/embedding execution, and other prohibited state transitions.

All 22 emit an exact `ROUND3H_NEGATIVE=...:PASS` marker. Semantic, retrieval,
query-plan, artifact-contract, and historical-migration freeze tests also pass.
