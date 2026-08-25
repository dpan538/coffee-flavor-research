# Database relationship model

Migrations 036–038 add eight entity types without a new schema:

| Table                                 | Role                                       | Rows |
| ------------------------------------- | ------------------------------------------ | ---: |
| `corpus.association_range`            | seven non-ontological candidate anchors    |    7 |
| `corpus.association_range_membership` | XOR-linked, evidence-bounded memberships   |   18 |
| `corpus.association_measurement`      | method-specific future quantitative ledger |    0 |
| `calibration.question_range_target`   | logical question-to-range hypotheses       |   18 |
| `audit.relationship_semantic_rule`    | executable relationship registry           |   34 |
| `audit.constraint_registry_entry`     | executable major-constraint registry       |   35 |
| `audit.forbidden_inference_rule`      | prohibited source-fact -> claim paths      |   14 |
| `audit.round3f_checkpoint`            | canonical and round prohibition receipt    |    1 |

`NEW_ENTITY_TYPE_COUNT=8`; `NEW_ENTITY_INSTANCE_COUNT=127`.

Membership links exactly one of normalized expression, text-first lexical
candidate, canonical concept or text candidate. It never requires a concept.
Partial unique indexes prevent duplicate same-range facts while permitting the
same subject in multiple ranges.

Range lifecycle triggers enforce source-local/cross-source distinction and the
review gate. Question checks hold validation, context and information-gain
states closed. Canonical post-row triggers freeze the ontology. A model-run
trigger rejects Round 3F/range input.

The existing text and JSONB structures remain intact. This is not a generic
relationship subsystem and no new schema, pgvector extension or embedding
store exists.
