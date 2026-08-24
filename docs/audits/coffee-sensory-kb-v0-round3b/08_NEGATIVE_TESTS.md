# Negative-test receipt

The Round 3B negative suite intentionally verifies failure of:

- five-level promotion;
- seven-level promotion missing medium-light;
- seven-level promotion missing medium-dark;
- duplicate ordinal position;
- unknown C0 family insertion;
- espresso-roast-to-dark mapping without approval;
- City+ arbitrary mapping without approval;
- historical V0 scheme modification;
- historical V0 category deletion; and
- frozen raw-context row modification.

Expected SQLSTATE/constraint pairs are asserted, not merely any exception. A
separate positive fixture proves unknown remains valid as an observation state.
The semantic validator separately proves unknown cannot be exposed through the
current C0 view. The suite rolls back every fixture.

`NEGATIVE_TEST_PASS=true`
