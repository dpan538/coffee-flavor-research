# Adapter quality audit

## Common output contract

The source-neutral `round3k.source-adapter.v1` contract accepts explicit records
for 11 source kinds: official HTML/auction HTML, official PDF catalog/results,
CSV, TSV, XLSX score export, JSON API payload, authorized Award Force or other
competition-platform export, and permitted transcript.

Every bundle must contain a manifest, checksums, and eleven tabular outputs for
series, edition, entry, coffee identity, preparation service, scores, descriptor
assertions, normalization, duplicate/repeat decisions, rights, and effective
record eligibility. The contract checks file inventory, schemas, row counts,
hashes, source authorization, explicit spans, referential integrity, rights,
quality status, and eligibility consistency.

## No-inference boundary

Adapters may copy explicit source fields and apply mechanical normalization.
They may not infer flavor from category, origin, process, variety, score, roast,
or other metadata; infer roast from filter/espresso/Nordic language; fabricate
fresh-preparation evidence; convert marketing notes to P1; or mark pending
rights as model-eligible. Numeric scores remain separate from descriptor text.

The included structural fixture is deliberately marked test-only,
`contains_observed_coffee_data=false`, and ineligible for core counting. It
proves shape, not acquisition.

## Quality thresholds and adversarial coverage

Before a real bundle can be validated, audited samples must meet entry identity
accuracy ≥0.99, score accuracy ≥0.99, descriptor-span precision ≥0.97,
false-flavor-document rate ≤0.02, and duplicate-linkage accuracy ≥0.98.
Adversarial tests cover missing/tampered files, unsupported kinds, unauthorized
exports, schema drift, source-span errors, semantic normalization, invalid
lineage, duplicate/repeat defects, quality inflation, rights inflation, and
fixture leakage.

No live source-specific bundle has been acquired or declared validated. The
contract exposes 11 generic source profiles and passes 49 tests, including 46
adversarial cases. The byte-reproducible structural fixture remains explicitly
ineligible for observed and model-eligible counts.
