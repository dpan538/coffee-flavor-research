# Model-prebuild expected-state result

Result: `COMPLETE_WITH_DATA_COVERAGE_GAP`. The frozen baseline and thresholds
were preserved with zero revisions. `Pass` is the deterministic result exposed
by `audit.run_model_prebuild_readiness_gate()`; preferred-only misses remain
visible even when they do not prevent a positive all-hard-gates decision.

| Readiness dimension                                 | Baseline | Minimum | Preferred | Observed |    Delta |      Pass      | Evidence path                                            |
| --------------------------------------------------- | -------: | ------: | --------: | -------: | -------: | :------------: | -------------------------------------------------------- |
| analysis.feature_registry                           |    false |    true |      true |     true |   gained |      PASS      | `evidence.v_model_prebuild_feature_availability`         |
| analysis.leakage_audit                              |    false |    true |      true |     true |   gained |      PASS      | `audit.model_prebuild_leakage_risk`                      |
| analysis.manifest                                   |    false |    true |      true |     true |   gained |      PASS      | `db/data/model-prebuild/v0/MODEL_PREBUILD_MANIFEST.json` |
| analysis.prebuild_only_guard                        |    false |    true |      true |     true |   gained |      PASS      | `audit.model_prebuild_execution_guard`                   |
| analysis.source_partitions                          |    false |    true |      true |     true |   gained |      PASS      | `evidence.v_model_prebuild_source_partitions`            |
| consumer.ordinary_user_source_count                 |        2 |       2 |         4 |        5 |       +3 |      PASS      | `audit.v_model_prebuild_coverage`                        |
| context.crossed_cell_count                          |        1 |      12 |        50 |      118 |     +117 |      PASS      | `audit.model_prebuild_context_cell`                      |
| context.empirical_coverage_cell_count               |       52 |     120 |       180 |      181 |     +129 |      PASS      | `audit.v_model_prebuild_coverage`                        |
| context.preparation_sensory_coverage                |        1 |       3 |         5 |        8 |       +7 |      PASS      | `audit.v_model_prebuild_coverage`                        |
| context.roast_sensory_coverage                      |        4 |       4 |         6 |        9 |       +5 |      PASS      | `audit.v_model_prebuild_coverage`                        |
| expected_state.threshold_revision_count             |        0 |       0 |         0 |        0 |        0 |      PASS      | `audit.model_prebuild_threshold_revision`                |
| governance.hashes                                   |     true |    true |      true |     true | retained |      PASS      | `audit.v_model_prebuild_rights_completeness`             |
| governance.rights                                   |     true |    true |      true |     true | retained |      PASS      | `audit.v_model_prebuild_rights_completeness`             |
| governance.source_annotation                        |     true |    true |      true |     true | retained |      PASS      | `audit.v_model_prebuild_rights_completeness`             |
| language.contemporary_source_family_count           |        0 |       3 |         5 |        0 |        0 |      FAIL      | `corpus.v_model_prebuild_language_inventory`             |
| language.new_contemporary_document_count            |        0 |     500 |     1,500 |        0 |        0 |      FAIL      | `corpus.v_model_prebuild_language_inventory`             |
| language.unique_expression_count                    |    1,777 |   2,500 |     3,500 |    1,777 |        0 |      FAIL      | `corpus.normalized_expression`                           |
| language.zh_hans_sensory_expression_count           |        0 |       0 |       200 |        0 |        0 | PREFERRED_FAIL | `corpus.v_model_prebuild_language_inventory`             |
| language.zh_hans_source_family_count                |        0 |       2 |         3 |        0 |        0 |      FAIL      | `corpus.v_model_prebuild_language_inventory`             |
| milk.sensory_outcome_source_family_count            |        0 |       0 |         1 |        2 |       +2 |      PASS      | `evidence.model_prebuild_source_profile`                 |
| quality.explicit_missingness_and_harmonization      |    false |    true |      true |     true |   gained |      PASS      | `evidence.model_prebuild_feature_definition`             |
| question.independent_research_target_count          |        2 |       6 |        10 |       12 |      +10 |      PASS      | `calibration.v_model_prebuild_question_evidence`         |
| question.information_gain_estimated_count           |        0 |       0 |         0 |        0 |        0 |      PASS      | `calibration.model_prebuild_question_evidence`           |
| question.user_validated_count                       |        0 |       0 |         0 |        0 |        0 |      PASS      | `calibration.model_prebuild_question_evidence`           |
| reference.panel_source_count                        |        1 |       2 |         3 |        4 |       +3 |      PASS      | `audit.v_model_prebuild_coverage`                        |
| relationship.cross_source_membership_count          |        0 |       3 |         6 |        4 |       +4 |      PASS      | `audit.v_model_prebuild_relationship_delta`              |
| relationship.evidence_claim_count                   |       20 |      80 |       150 |       96 |      +76 |      PASS      | `audit.v_model_prebuild_relationship_delta`              |
| relationship.range_with_cross_source_evidence_count |        0 |       0 |         4 |        3 |       +3 | PREFERRED_FAIL | `audit.model_prebuild_range_evidence_summary`            |
| relationship.range_with_source_local_evidence_count |        1 |       5 |         5 |        6 |       +5 |      PASS      | `audit.model_prebuild_range_evidence_summary`            |
| relationship.source_local_membership_count          |        1 |       6 |        10 |        6 |       +5 |      PASS      | `audit.v_model_prebuild_relationship_delta`              |
| sensory.method_family_count                         |        3 |       3 |         4 |        4 |       +1 |      PASS      | `evidence.model_prebuild_source_profile`                 |
| sensory.source_family_count                         |        4 |       5 |         8 |        9 |       +5 |      PASS      | `audit.v_model_prebuild_coverage`                        |

Descriptive inventory deltas outside the readiness-gate rows are: sensory
rows 3,689→4,344; samples/configurations 101→230; and disclosed participants
or panelists 236→520. Language did not improve. Therefore the all-hard-gates
rule correctly remains false despite every non-language hard gate passing.
