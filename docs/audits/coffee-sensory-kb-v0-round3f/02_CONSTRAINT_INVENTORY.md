# Constraint inventory receipt

PostgreSQL catalog: 199 PK, 378 FK, 243 unique/candidate-key, 550 check, 14
constraint-trigger entries and 138 triggers.

Semantic registry: 35 major rules.

| Enforcement layer     | Count |
| --------------------- | ----: |
| PostgreSQL constraint |    15 |
| PostgreSQL trigger    |    10 |
| audit query           |     2 |
| CI gate               |     4 |
| curation policy       |     4 |

Thirty-three semantic rules are enforced and two future packaging/review rules
are documented only. No registered rule is missing-but-enforceable or
unresolved.

`CONSTRAINT_REGISTRY_COUNT=35`

`DATABASE_ENFORCED_CONSTRAINT_COUNT=25`

`AUDIT_ENFORCED_CONSTRAINT_COUNT=2`

`DOCUMENTED_BOUNDARY_COUNT=4`
