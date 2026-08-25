# Database forward changes

Round 3F adds three forward migrations:

- `036_round3f_relationship_constraint_contract.sql`: eight minimal entity
  types, controlled values, lifecycle/non-inference/canonical/model gates;
- `037_round3f_relationship_seed.sql`: seven candidate anchors, 18 memberships,
  18 question targets, registries and checkpoint;
- `038_round3f_views_validation.sql`: indexes, four read models, delta and
  coverage views, and 23 validation queries.

No prior migration was changed. No new schema, canonical concept, canonical
relation type, frontend component, model, embedding or pgvector dependency was
added.

`FORWARD_MIGRATION_COUNT=3`

`NEW_ENTITY_TYPE_COUNT=8`

`NEW_ENTITY_INSTANCE_COUNT=127`

`NEW_RELATION_TYPE_COUNT=8`

`NEW_RELATION_INSTANCE_COUNT=36`
