# C0 user projection validation

`PRODUCT_C0_MANDATORY=true`

`PRODUCT_C0_UNKNOWN_OPTION=false`

`CURRENT_USER_C0_FAMILY_COUNT=8`

`context.v_current_user_preparation` returns filter/percolation, immersion,
hybrid, espresso/pressure, espresso + water, stovetop/boiled, cold extraction,
and espresso + milk in deterministic order with candidate English and
Simplified Chinese labels. It does not derive options from the observation
status table.

Validation rejects any top-level family with an unknown/unsure/not-reported/
unresolved/not-applicable identity or label. A positive transaction-local test
also inserts an observation with preparation and roast status `unknown`,
proving that the database observation state remains legal while the user
projection excludes it.
