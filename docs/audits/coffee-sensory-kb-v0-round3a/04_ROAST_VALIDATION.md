# Roast validation

## Inventory

```text
ROAST_SCHEME_COUNT=4
RECOMMENDED_USER_ROAST_LEVEL_COUNT=5
UNRESOLVED_ROAST_LABEL_COUNT=13
SEVEN_LEVEL_ROAST_HYPOTHESIS=rejected_for_v1_use_five_coarse_levels
```

## Scheme isolation

The project five-level scheme is the single normalized target. The common three-level scheme maps approximately. Traditional trade terms and brew-intent terms are unordered and have no active normalization.

Validated invariants:

- exactly one project target scheme;
- exactly five current target categories;
- contiguous ordinal positions 1–5;
- no ordinal positions on terminology schemes;
- every normalization target belongs to the project scheme;
- Nordic roast remains unresolved;
- espresso roast does not map to dark;
- unknown roast is a status, not a scheme category;
- no measurement-to-category cutoff table exists.

## Measurement safety

Whole-bean and ground Agtron-method records are separate. Whole-bean and ground CIELAB L\* records are separate. Bounds are method declarations, not sensory values. A transaction-local Agtron value of 151 fails `observation_roast_measurement_bounds_ck`.

## Negative cases

- adding an ordinal to the trade scheme fails `roast_category_scheme_ordinal_ck`;
- using a common-scheme category as a normalized target fails `roast_category_mapping_target_ck`;
- a known observation without a normalized value fails the observation check;
- conflicting exact lexical senses require explicit ambiguity.

All checks pass in `audit.run_round3a_validation_queries()` and the Round 3A SQL suites.
