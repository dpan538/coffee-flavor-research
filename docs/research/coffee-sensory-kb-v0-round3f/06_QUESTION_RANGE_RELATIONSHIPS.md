# Question-range relationships

The governed inventory contains 15 logical questions and 30 language versions.
The 18 target rows below are logical-question relations, not language-equivalence
claims. Every context status is `HYPOTHESIZED`, user validation is
`NOT_USER_VALIDATED`, and information gain is `NOT_ESTIMABLE`.

| Logical question          | Range target(s)                                         | Direction                   | Option/range overlap finding                                                                                      |
| ------------------------- | ------------------------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `family_direction`        | floral/tea; fruit; cocoa/nut/caramel; roast/spice/smoke | cross-range broad direction | `cocoa_roast` intentionally indicates two nearby ranges                                                           |
| `fruit_direction`         | fruit                                                   | within range                | citrus, berry, dried/tropical are candidate options                                                               |
| `sweet_direction`         | sweet-associated                                        | within range                | caramel, honey/floral and vanilla remain non-equivalent options                                                   |
| `roast_direction`         | roast/spice/smoke                                       | within range                | cocoa/nut option overlaps another range conceptually but is not given a second target without a separate decision |
| `bright_acidity`          | acidity character                                       | within range                | citrus and juicy can also have evidence-bounded memberships elsewhere                                             |
| `texture_direction`       | texture/body/drying                                     | within range                | tea-like and juicy illustrate modality overlap                                                                    |
| `floral_tea_reference`    | floral/tea                                              | within range                | named references remain familiarity-dependent                                                                     |
| `tea_style_reference`     | floral/tea                                              | within range                | Earl Grey/bergamot/black tea/citrus peel are not synonyms                                                         |
| `fruit_region_reference`  | fruit                                                   | within range                | broad region refinement only                                                                                      |
| `cocoa_nut_reference`     | cocoa/nut/caramel                                       | within range                | cocoa, dark chocolate and nuts not collapsed                                                                      |
| `browned_sweet_reference` | cocoa/nut/caramel                                       | within range                | caramel, brown sugar and honey overlap but differ                                                                 |
| `roast_smoke_reference`   | roast/spice/smoke                                       | within range                | response is not roast-level context                                                                               |
| `sweetness_character`     | sweet-associated                                        | within range                | taste and association remain distinct                                                                             |
| `acidity_character`       | acidity character                                       | within range                | bright/juicy/citrus/sour not validated constructs                                                                 |
| `texture_character`       | texture/body/drying                                     | within range                | clean omitted pending construct review                                                                            |

`QUESTION_LOGICAL_COUNT=15`

`QUESTION_LANGUAGE_VERSION_COUNT=30`

`QUESTION_RANGE_TARGET_COUNT=18`

`QUESTION_USER_VALIDATED_COUNT=0`

`QUESTION_INFORMATION_GAIN_ESTIMATED_COUNT=0`
