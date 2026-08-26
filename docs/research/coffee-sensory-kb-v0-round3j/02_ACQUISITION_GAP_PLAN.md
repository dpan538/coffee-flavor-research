# Round 3J acquisition-gap plan

This plan starts from the immutable `coffee-sensory-research-db-v0.1.0`
checkpoint at `c3ae9b880d85507a0b8b0298bb94ef013d02f928`. The expected-state contract was
committed as `2dd6b47f3301b4f705bf6624c69c2832eda17527` and passed both remote CI jobs
before candidate discovery began. No v0.1.0 member, snapshot, migration, current
view, manifest, or tag may be changed.

## Targeted gaps

Round 3J uses six acquisition batches. Every candidate is named in
`db/data/round3j/source_candidate_register.tsv` before a raw file is acquired.
Metadata search alone does not confer admission, rights, independence, or
training eligibility.

| Batch | Target                             |                                                   Minimum gap at start | Material gain unit                                                                             |
| ----- | ---------------------------------- | ---------------------------------------------------------------------: | ---------------------------------------------------------------------------------------------- |
| A     | Contemporary tasting language      |        3 families; 2,711 documents; 3,004 governed expressions overall | Independent rights-cleared family, qualifying document, or governed source-authored expression |
| B     | Source-authored Simplified Chinese |                                    2 families; 251 sensory expressions | Independent zh-Hans family or reviewed source-authored sensory expression                      |
| C     | Sensory/sample scale               | 3 families; 270 sample/configuration units before effective-unit audit | Independent coffee/sample/configuration with source-local outcome semantics                    |
| D     | Crossed context                    |                                     Effective baseline not yet audited | Observed preparation-by-roast cell or leakage-safe coffee/sample group                         |
| E     | Relationship density               |            53 claims; 2 cross-source memberships; 1 cross-source range | Reviewed source-qualified support, challenge, mixed, or insufficient claim                     |
| F     | Long-tail closure                  |                           To be derived from the training-corpus audit | Rare target, language, ambiguity, abstention, or under-covered context stratum                 |

Raw-row growth is reported separately from effective-unit, family, coverage,
and unique-expression gains. Repetition, mirrors, template variants, machine
translations, and project-authored lexical variants do not close a gap.

## Search and admission order

1. Search named official repositories, journal supplements, institutional
   repositories, PMC, Data in Brief, or versioned upstream releases.
2. Record the named candidate, exact stable locator, expected contribution,
   access state, preliminary rights state, and independence basis.
3. Review explicit license/terms, privacy, third-party material, upstream
   provenance, and model-research use.
4. Authorize raw acquisition only for candidates whose locator and review
   support it; hash every acquired file before transformation.
5. Preserve raw and governed artifacts separately, record exclusions, and
   evaluate task-specific eligibility without treating admission as a gold
   training label.

Unclear rights yield `BLOCKED_RIGHTS` or `METADATA_ONLY`. Mirrors remain tied to
one canonical upstream family. Generic search-result pages, public visibility,
and downloadable files are never sufficient evidence of reuse permission.

## Stop rule

Acquisition stops when the Round 3 exit gate passes or after three consecutive
targeted batches produce no material gain toward any failed readiness gate.
Thresholds remain unchanged (`EXPECTED_STATE_THRESHOLD_REVISION_COUNT=0`).
