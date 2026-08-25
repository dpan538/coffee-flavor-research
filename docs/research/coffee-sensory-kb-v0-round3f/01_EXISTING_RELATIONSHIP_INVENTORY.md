# Existing relationship inventory

The read-only inventory covered `ref`, `kb`, `evidence`, `corpus`, `context`,
`calibration`, `ml` and `audit`. Relation-like columns were not treated as
defects merely because they are text or JSONB.

| Schema        | Base tables | Relation-like columns | Dominant classification                                 | Retention decision                                          |
| ------------- | ----------: | --------------------: | ------------------------------------------------------- | ----------------------------------------------------------- |
| `ref`         |          41 |                    13 | normalized typed relation / governance vocabulary       | retain typed codes                                          |
| `kb`          |           6 |                    30 | normalized typed relation                               | retain canonical graph and lexicalization                   |
| `evidence`    |          24 |                    74 | normalized support + JSONB research metadata            | retain JSONB where source metadata varies                   |
| `corpus`      |          35 |                    79 | source-local measurement + text-first research relation | retain preserved expressions and method-specific statistics |
| `context`     |          25 |                    58 | normalized context taxonomy + source-local mapping      | retain separate from sensory ontology                       |
| `calibration` |          35 |                    45 | normalized study relation + JSONB question research     | retain JSONB candidate options/eligibility                  |
| `ml`          |          11 |                    29 | governed model-run/retrieval relation                   | retain; no Round 3F run                                     |
| `audit`       |          22 |                    44 | governance relation / prohibition                       | extend with registries and checkpoint                       |

## Classification examples

| Current structure                                       | Classification               | Why retained or changed                                              |
| ------------------------------------------------------- | ---------------------------- | -------------------------------------------------------------------- |
| `kb.concept_relation`                                   | NORMALIZED_TYPED_RELATION    | six controlled canonical predicates with support and graph semantics |
| `kb.lexicalization`                                     | NORMALIZED_TYPED_RELATION    | reviewed expression-to-concept assertion; separate from candidates   |
| `corpus.lexical_mapping_candidate`                      | TEXT_FIRST_RESEARCH_RELATION | partial/composite/ambiguous mappings must not require one concept    |
| question `answer_options`, `eligible_c0/c1`, `evidence` | JSONB_RESEARCH_RELATION      | candidate-specific shapes remain versioned research material         |
| pair-measurement tables                                 | SOURCE_LOCAL_MEASUREMENT     | values retain corpus, method, scale and context                      |
| support and review tables                               | GOVERNANCE_RELATION          | provenance and promotion remain explicit                             |
| model/collection prohibition flags                      | PROHIBITION                  | hard round boundaries                                                |
| `co_selected_with`                                      | UNRESOLVED                   | no admitted instance or protocol in current data                     |

The registry view reports 34 relationship types and 17,512 instances. That
count is an inventory, not a quality metric.
