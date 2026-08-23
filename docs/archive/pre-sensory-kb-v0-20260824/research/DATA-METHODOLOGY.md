# Data Methodology

## Schema

Descriptor data lives in `packages/flavor-data/src/descriptors.ts` and is validated by `packages/flavor-data/src/schema.ts`.

Each descriptor includes stable `id` and `slug`, English and Simplified Chinese labels, bilingual aliases, category and descriptor status, sensory modalities, original bilingual summaries, six sensory association ranges, confidence, evidence status, source IDs, visual profile parameters, and optional editorial notes.

The six range dimensions are sourness, sweetness, bitterness, aroma prominence, body, and roast/fermentation association.

Every range stores `min`, `typical`, and `max` values from 0 to 5. Validation rejects values outside 0-5 and rejects ranges where `min > typical` or `typical > max`.

## Prototype Score Status

The current values are sensory association profiles, not chemical analysis, official cupping scores, or fixed measurements for any coffee.

All MVP scores are marked as `project_curated_draft`. They exist to test whether the interface can show uncertainty, comparison, and a two-dimensional map without pretending to be authoritative.

## Source Registry

Sources live in `packages/flavor-data/src/sources.ts`.

Initial source entries:

- WCR Sensory Lexicon: reference framework, reference-only.
- SCA Coffee Value Assessment: reference framework, reference-only.
- UC Davis Black Coffee Consumer Dataset: open dataset candidate for future validation.
- Coffee Flavor Atlas Editorial Pilot: project-created draft source for the current MVP.

The MVP does not copy protected definitions, full vocabulary lists, graphics, forms, or long passages from these sources.

## Evidence Status

- `reference_supported`: future state for fields supported by a cited reference framework.
- `open_data_supported`: future state for fields computed or checked against open data.
- `project_curated_draft`: current MVP state for project-created prototype values.
- `unresolved`: content that should remain visible but not be treated as stable.

## Confidence

- `high`: low ambiguity inside the pilot vocabulary.
- `medium`: useful but likely to shift with validation.
- `low`: boundary, compound, culturally sensitive, or unresolved.

## Translation Limits

Chinese labels and aliases are project editorial choices. They are useful for bilingual search and layout testing, but they should be reviewed by bilingual coffee sensory practitioners before being treated as stable terminology.

## Future Replacement Path

1. Define a documented scoring protocol.
2. Record source license and reuse permissions.
3. Add processing scripts or reviewer notes.
4. Recompute ranges from documented evidence.
5. Update `evidenceStatus` only for fields actually supported by that evidence.
6. Keep editorial notes where translation or category boundaries remain uncertain.
