# Lexical candidate and range analysis

`corpus.lexical_mapping_candidate` remains unchanged with 107 rows and text
columns `candidate_mapping`, `evidence_key`, `mapping_scope` and
`ambiguity_note`. No `concept_id NOT NULL` was added.

All 107 rows have preparation-only scope and therefore resolve in
`corpus.v_lexical_candidate_range_disposition` as
`OUTSIDE_CURRENT_RANGE_MODEL`. This is not an error and does not trigger an
`OTHER` range.

Round 3F admits 18 sensory-range memberships through preserved Round 2B
normalized expressions (16) or exact text-only governed question options (2).
No current `lexical_mapping_candidate` row was forced into a sensory range.

| Range                   | Memberships | Evidence boundary                                                                  |
| ----------------------- | ----------: | ---------------------------------------------------------------------------------- |
| floral / tea            |           4 | governed `family_direction`, `floral_tea_reference`, `tea_style_reference` wording |
| fruit                   |           2 | governed `fruit_direction` options                                                 |
| cocoa / nut / caramel   |           4 | governed cocoa/nut and browned-sweet candidates                                    |
| roast / spice / smoke   |           1 | governed roast option                                                              |
| sweet-associated        |           2 | governed sweet options                                                             |
| acidity character       |           2 | governed bright/acidity options                                                    |
| texture / body / drying |           3 | governed texture options                                                           |

Four preserved expressions have two ranges: `caramel`, `honey`, `citrus` and
`juicy`. The eight participating rows demonstrate non-exclusive storage only.
They do not assert semantic equivalence or sensory probability.
