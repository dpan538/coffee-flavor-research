# Non-inference negative tests

All operations ran inside rollback-only transactions.

| Test                                         | SQLSTATE | Exact constraint/validation failure              |
| -------------------------------------------- | -------- | ------------------------------------------------ |
| recurrent expression automatic promotion     | 23514    | `lexicalization_round3e_candidate_approval_ck`   |
| range co-presence to synonym                 | 23514    | `round3f_range_not_synonym_ck`                   |
| co-occurrence to sensory neighbour           | 23514    | `round3f_cooccurrence_not_neighbour_ck`          |
| exclusive range membership                   | 23514    | `association_range_membership_nonprobability_ck` |
| unresolved candidate forced to concept       | 23514    | `association_range_membership_subject_xor_ck`    |
| source-local range mislabeled cross-source   | 23514    | `association_range_cross_source_support_ck`      |
| question active without user evidence        | 23514    | `question_research_user_validation_evidence_ck`  |
| information gain without observations        | 23514    | `question_range_target_nonvalidation_ck`         |
| source absence to negative relation          | 23514    | `round3f_absence_not_negative_ck`                |
| new canonical concept from phrase            | 23514    | `round3f_canonical_ontology_frozen_ck`           |
| split existing descriptor                    | 23514    | `round3f_canonical_ontology_frozen_ck`           |
| Round 3F data in model run                   | 23514    | `round3f_model_run_prohibited_ck`                |
| numeric probability membership               | 23514    | `association_range_membership_nonprobability_ck` |
| pairwise chain to transitive association     | 23514    | `round3f_association_not_transitive_ck`          |
| literal translation to bilingual equivalence | 23514    | `round3f_translation_not_equivalence_ck`         |
| range active without review                  | 23514    | `association_range_calibration_review_ck`        |
| measurement without method configuration     | 23514    | `association_measurement_configuration_ck`       |
| new canonical relation type                  | 23514    | `round3f_canonical_ontology_frozen_ck`           |

`NEW_NEGATIVE_TEST_COUNT=18`

`CONSTRAINT_TEST_PASS=true`

`FORBIDDEN_INFERENCE_TEST_PASS=true`
