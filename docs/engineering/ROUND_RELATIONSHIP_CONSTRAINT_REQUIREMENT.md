# Round relationship and constraint requirement

Effective from Round 3F. Historical rounds are not rewritten retroactively.

Every substantive future round must add:

`docs/audits/<round-name>/RELATIONSHIP_CONSTRAINT_DELTA.md`

The file is a promotion gate and must report exact counts or `UNRESOLVED` for:

- new entity types and instances;
- new relationship types and instances;
- modified and deprecated relationship semantics;
- new, modified and removed constraints;
- new promotion gates and forbidden inference paths;
- unresolved relationship questions;
- text-only and JSONB relationships retained intentionally.

The delta must also state whether canonical concepts were added, split, merged,
retyped or deprecated and whether any automatic promotion path exists. A zero
is a substantive result; omission is not.

## Required template

```text
ROUND=
SOURCE_SHA=

NEW_ENTITY_TYPE_COUNT=
NEW_ENTITY_INSTANCE_COUNT=
NEW_RELATION_TYPE_COUNT=
NEW_RELATION_INSTANCE_COUNT=

MODIFIED_RELATION_SEMANTIC_COUNT=
DEPRECATED_RELATION_SEMANTIC_COUNT=

NEW_CONSTRAINT_COUNT=
MODIFIED_CONSTRAINT_COUNT=
REMOVED_CONSTRAINT_COUNT=

NEW_PROMOTION_GATE_COUNT=
NEW_FORBIDDEN_INFERENCE_PATH_COUNT=
AUTOMATIC_PROMOTION_PATH_COUNT=

UNRESOLVED_RELATIONSHIP_COUNT=
TEXT_ONLY_RELATIONSHIP_COUNT=
JSONB_RELATIONSHIP_COUNT=

CANONICAL_CONCEPT_SPLIT_COUNT=
CANONICAL_CONCEPT_MERGE_COUNT=
CANONICAL_CONCEPT_RETYPE_COUNT=
```

The owning audit must explain counting boundaries, provenance coverage and why
text/JSONB was retained. Higher edge count is never described as higher
scientific correctness.
