# Round 3F relationship and constraint delta

Counting boundary: entity instances are rows in the eight new tables; new
relationship instances are the 18 range memberships plus 18 question-range
targets. Registered existing types/instances are inventory, not new semantics.

```text
ROUND=coffee-sensory-kb-v0-round3f
SOURCE_SHA=eee5c140fb6d3ab61f87dfe472601aac2e4c39cf

NEW_ENTITY_TYPE_COUNT=8
NEW_ENTITY_INSTANCE_COUNT=127

NEW_RELATION_TYPE_COUNT=8
NEW_RELATION_INSTANCE_COUNT=36

MODIFIED_RELATION_SEMANTIC_COUNT=0
DEPRECATED_RELATION_SEMANTIC_COUNT=0

RELATION_WITH_PROVENANCE_RATE=1.0000

NEW_CONSTRAINT_COUNT=25
MODIFIED_CONSTRAINT_COUNT=0
REMOVED_CONSTRAINT_COUNT=0
NEW_NEGATIVE_TEST_COUNT=18

NEW_PROMOTION_GATE_COUNT=3
NEW_FORBIDDEN_INFERENCE_PATH_COUNT=14
AUTOMATIC_PROMOTION_PATH_COUNT=0

UNRESOLVED_RELATIONSHIP_COUNT=1
TEXT_ONLY_RELATIONSHIP_COUNT=109
JSONB_RELATIONSHIP_COUNT=233
INTENTIONALLY_UNNORMALIZED_RELATIONSHIP_COUNT=342

CANONICAL_CONCEPT_SPLIT_COUNT=0
CANONICAL_CONCEPT_MERGE_COUNT=0
CANONICAL_CONCEPT_RETYPE_COUNT=0
```

`TEXT_ONLY_RELATIONSHIP_COUNT` is 107 lexical candidate rows plus two text-only
range memberships. `JSONB_RELATIONSHIP_COUNT` is 18 question-research rows plus
215 external-expression rows retaining candidate arrays. The structures are
intentionally method/source local; they are not normalization debt.
