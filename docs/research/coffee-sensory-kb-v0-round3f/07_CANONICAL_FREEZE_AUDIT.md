# Canonical freeze audit

Source checkpoint: `eee5c140fb6d3ab61f87dfe472601aac2e4c39cf`.

| Assertion                       | Before | After | Result |
| ------------------------------- | -----: | ----: | ------ |
| total canonical concepts        |    130 |   130 | pass   |
| active sensory attributes       |     92 |    92 | pass   |
| new canonical concepts          |      0 |     0 | pass   |
| splits                          |      0 |     0 | pass   |
| merges                          |      0 |     0 | pass   |
| retypes                         |      0 |     0 | pass   |
| deprecations                    |      0 |     0 | pass   |
| canonical relation-type changes |      0 |     0 | pass   |

`audit.round3f_checkpoint`, an audit query and post-row freeze triggers prevent
Round 3F insert/update/delete of `kb.concept` and `ref.relation_type`. The
post-row timing preserves earlier constraint tests while still rolling back any
otherwise valid mutation.

## ONTOLOGY_CHANGE_CANDIDATE_REGISTER

No candidate recorded. `REGISTER_COUNT=0`.

Any future candidate must remain a proposal until an explicit ontology round
with provenance, review and a relationship/constraint delta.
