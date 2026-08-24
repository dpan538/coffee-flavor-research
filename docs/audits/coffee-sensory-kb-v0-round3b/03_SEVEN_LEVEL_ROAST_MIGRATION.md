# Seven-level roast migration receipt

`CURRENT_SCHEME=roast.scheme.project_v1_seven_level`

`CURRENT_USER_ROAST_LEVEL_COUNT=7`

The active projection is exactly:

1. `extremely_light`
2. `light`
3. `medium_light`
4. `medium`
5. `medium_dark`
6. `dark`
7. `extremely_dark`

All rows report `scale_semantics=ordinal_not_interval`. The schema has no
distance, interval, or equal-step column. Promotion triggers reject a scale
with fewer than seven active categories or without medium-light, medium, and
medium-dark.

`roast.scheme.project_v0_five_level` remains with five immutable categories,
is marked deprecated/non-current, and is explicitly superseded by V1. The
Round 3A coverage view and validator remain pinned to V0 history.
