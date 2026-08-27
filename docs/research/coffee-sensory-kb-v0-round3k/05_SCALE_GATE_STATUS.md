# Scale gate status

## Gate evaluation

`SCALE_GATE.tsv` and the database gate views define the criteria. Current corpus
counts are zero, so none of the 1,000, 3,000, 7,000, or 10,000 gates passes.
Rates with a zero denominator are `NA`/`NOT_EVALUATED`, never 0% and never a
vacuous pass.

| Gate   | Required population                                                | Current status                 |
| ------ | ------------------------------------------------------------------ | ------------------------------ |
| 1,000  | observed P1/P2 effective round-service records plus pipeline proof | Not met                        |
| 3,000  | observed P1/P2 records plus expanded diversity/coverage            | Not met                        |
| 7,000  | research-grade observed corpus and all provenance/diversity gates  | Not met                        |
| 10,000 | rights-cleared, label-governed, reproducible freeze candidate      | Not met                        |
| 12,000 | forensic audit trigger                                             | Not triggered; no pass claimed |

## Scientific interpretation

The 7,000 milestone is not training readiness. It requires at least 7,000
observed core records and 40,000 non-score professional descriptor assertions,
plus source-family, preparation, C1, repeat, provenance, and holdout criteria.
Model-use rights may still be pending at that milestone.

The 10,000 milestone requires at least 10,000 model-eligible records, 60,000
descriptor assertions, affirmative model-research rights for every candidate,
complete governed label provenance, required review strata, source-family
diversity, category/C1 coverage, deterministic grouped splits, zero leakage, and
reproducibility. It authorizes only a later Round 4; it does not mean that a
model has been trained.

Current concentration, distinct-entry ratio, fresh-preparation provenance,
source provenance, file-hash completeness, rights completeness, label
provenance, and model-rights rates are undefined because no record is admitted.
The zero split-leak counts are marked `VACUOUS_ZERO` and do not satisfy the
10,000 gate.

The 12,000 forensic audit is not required at zero records. Its non-triggered
state must remain distinct from a successful forensic audit.
