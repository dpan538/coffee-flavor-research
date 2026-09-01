# Test classification and equivalence

The machine-readable inventory is
`db/data/ci/CI_TEST_CLASSIFICATION_AND_EQUIVALENCE.json`. It maps all 17
existing CI verification contracts to a new command, class, required inputs,
expected outputs, and asserted coverage.

```text
CLASSIFICATION_COUNT=17
MANDATORY_TEST_SKIP_COUNT=0
PUSH_REQUIRED_CURRENT_COUNT=15
RESTRICTED_LOCAL_REQUIRED_COUNT=1
SCHEDULED_HISTORICAL_COUNT=1
UNCLASSIFIED_TEST_COUNT=0
```

The historical entrypoint retains the former public CI command sequence:
public fixture replay, all named public artifact contracts, the explicit
restricted-input declaration, and `rebuild-twice.sh`. The new push entrypoints
divide it into an artifact path and one clean database path; neither deletes a
test command. `test-ci-workflow-contract.py` fails if an inventory row is
missing, a class is invalid, a public test token is absent, the historical
rebuild disappears, a restricted replay becomes permissive, or the workflow
loses a bounded push job or dispatchable historical workflow.

Restricted real-input replay was never a public GitHub Actions pass because
the owner-controlled data is intentionally unavailable there. It now has an
explicit `RESTRICTED_LOCAL_REQUIRED` command that requires the root and fails
closed if it is not supplied. This changes an implicit non-execution into an
auditable local release requirement; it does not treat absence as a negative
label or a public CI success.
