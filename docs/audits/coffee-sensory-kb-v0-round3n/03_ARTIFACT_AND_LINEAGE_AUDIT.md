# Artifact and lineage audit

`db/data/product-inference-v0/` contains exactly 15 public-safe files. The
manifest records SHA-256 hashes for 12 authoritative inputs, including the
database-backed context contract, public candidate distribution, governed
semantic artifacts, Round 3H structured evidence, Round 3M C0/C1 receipt, and
the bilingual public pilot labels. The twelfth input is the governed Round 3H
source-candidate register used for the bounded 30-candidate acquisition review.

Every candidate, prior, axis, effect, case, result, explanation, and owner
review item contains a lineage field. Generated files reference stable IDs and
paths rather than copying the 30–70 MB historical ledgers. `SHA256SUMS` covers
all other product files and is itself excluded from recursive hashing.

No historical artifact path is an output target. The generator deletes and
recreates files only inside `db/data/product-inference-v0/`. Re-running it
leaves all 15 bytes unchanged.

```text
PRODUCT_ARTIFACT_COUNT=15
AUTHORITATIVE_INPUT_HASH_COUNT=12
PROVENANCE_MISSING_COUNT=0
CHECKSUM_PASS=true
HISTORICAL_ARTIFACT_OVERWRITE_COUNT=0
```
