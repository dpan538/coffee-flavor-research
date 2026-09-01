# CI negative and invariant tests

The CI decomposition is protected by `db/scripts/test-ci-workflow-contract.py`.
It passes locally with 18 classified contracts and zero mandatory skips.

Its invariant checks reject:

- a missing, duplicate, or unclassified historical/current contract;
- removal of any named public artifact test from the push entrypoint;
- removal of `rebuild-twice.sh` from the historical entrypoint;
- a restricted replay that does not require owner-controlled input;
- a current database path that omits migration, artifact load, or SQL tests;
- removal of a bounded push job; and
- a historical workflow without dispatch, schedule, the original historical
  command, or its documented dedicated budget.

The existing database contracts continue to test negative SQL, semantic,
retrieval, query-plan, artifact checksum, public-boundary, and restoration
conditions. No SQL assertion was removed.

`test-product-inference-v0.py` additionally rejects restricted leakage,
missing lineage, unknown concepts, untraceable rights, incomplete checksums,
historical input drift, alias/near-duplicate outputs, review-only primary
promotion, non-neutral missing context, inferred roast, non-mention negatives,
unhandled conflicts/open set, forced slot filling, missing explanations,
rights-blocked output, unsupported questions, fabricated owner review, model
files, or non-reproducible generation.

The same test requires lineage on every row of every product TSV, computed
rather than narrative-only ablation metrics, at most 30 bounded-acquisition
candidates, zero new imports, all ten requested owner-review categories, blank
owner decisions, and explicit allowed review vocabularies.

```text
PRODUCT_NEGATIVE_TEST_PASS=true
RIGHTS_LEAK_COUNT=0
ALIAS_DUPLICATE_OUTPUT_COUNT=0
NEAR_DUPLICATE_OUTPUT_COUNT=0
UNREVIEWED_PRIMARY_RELATION_COUNT=0
```
