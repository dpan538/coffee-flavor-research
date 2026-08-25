# Reproducibility

PostgreSQL 17.11 applied all 33 migrations and ran the complete historical
through Round 3D suite twice from `template0`. Both disposable databases were
removed. Fourteen paired artifacts matched byte-for-byte.

```text
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
MIGRATION_MANIFEST_SHA256=df3c0bea7bbb74196ed13b8e9024cc5ef7df93b967a82050b0926bccab7e227c
SCHEMA_SHA256=53a33ba1e23ce7bf613cde224a4f25a1a7d2cc96829411fd3f784ddce2d7032d
VALIDATION_RESULTS_SHA256=b9d4cc74f2e5f030f494f34a4d94b1f0bca29649f298b97058cd49028aa268e2
ROUND3D_INVENTORY_SHA256=e0ed382f09a38ca9f65ab0c6bc4ce4aa4b64c1158dddc9dbaf6f05bdd2b33d7b
```

Deterministic generation also reproduced the matrix, randomization, question
assignment, protocol, split inventory, and release-manifest hashes.
