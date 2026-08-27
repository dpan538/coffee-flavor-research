# Effective record count audit

## Current authoritative counts

`EFFECTIVE_RECORD_METRIC.tsv` reports zero admitted competition series, zero
admitted editions, zero independent source families, zero observed P1/P2 core
records, zero model-eligible core records, and zero P3/P4 auxiliary records.
Coffee identities, entry services, round services, judge observations,
descriptor assertions, structured scores, and P1/P2 coassertion events are also
zero.

The separate planning inventories contain 24 series and 50 editions, all with
zero acquired records. Those counts are not substituted into database metrics.

## Count protections

An effective record requires one unique competition series, edition, category,
round, entry-or-lot, and preparation service, plus fresh-preparation evidence,
official P1/P2 professional evidence, an explicit score or descriptor payload,
admitted source and immutable hash lineage, and sufficient internal-research
rights. Model eligibility adds affirmative model-research rights, governed
labels, integrity, diversity, split, and reproducibility requirements.

Judge rows, numeric score rows, descriptor occurrences, mirror pages, and
repeated captures do not create effective records. Structured scores are reported
separately and do not inflate the professional descriptor assertion count.

## Zero-denominator treatment

Distinct-entry-service ratio, largest-family share, fresh-preparation provenance,
source provenance, file-hash completeness, rights completeness, model-rights
rate, and label-provenance rate are `NA`/`NOT_EVALUATED`. Zero split leakage is
`VACUOUS_ZERO`. None of these states is a pass.
