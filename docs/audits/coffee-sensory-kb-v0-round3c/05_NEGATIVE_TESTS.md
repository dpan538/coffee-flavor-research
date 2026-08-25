# Negative tests

`db/tests/round3c_negative.sql` proves rejection of:

- duplicate sample identity;
- invalid C0 family and C1 category;
- removal of a required seven-level roast distinction;
- direct participant identifier leakage;
- an active question with an invalid option count;
- assignment of an ineligible question;
- selection count above response cardinality;
- missing protocol and mismatched sample linkage;
- duplicate randomized session position;
- derived consensus presented as a raw observation;
- model output presented as canonical sensory knowledge;
- coffee-lot leakage across grouped splits; and
- a public release without manifest, checksum, license, rights, and split data.

All expected SQLSTATE and named-constraint assertions passed on PostgreSQL 17.
Semantic, retrieval, and query-plan contracts passed. The seeded database has
no assessors, presentations, responses, or sensory observations.
