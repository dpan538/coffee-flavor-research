# Coffee Sensory Context Calibration Dataset specification V0

Status: protocol and schema design; no real observation release exists

Provisional public artifact title: **Coffee Sensory Context Calibration
Dataset**

## Intended uses

The dataset is designed to support context-plausibility estimation, adaptive
question selection, answer-to-descriptor association, candidate-ranking
calibration, uncertainty and abstention evaluation, black/milk comparison, and
future reproducible benchmarks.

It is not designed to provide one objective flavor label per coffee.

## Claim-layer separation

The following layers are stored separately and never silently promoted:

```text
coffee and condition identity
sensory panel observations
ordinary-user question responses
derived consensus/reference distributions
roaster or industry descriptions
model outputs
evaluation judgments
```

Raw human observations belong only in raw response tables. Derived consensus
belongs in versioned analysis outputs. Model candidates belong in model-output
tables. Neither may be inserted as canonical ontology knowledge.

## Core entities

The PostgreSQL `calibration` schema governs:

- study and protocol versions;
- analysis plans and release snapshots;
- coffee lots and roast batches;
- preparation conditions and beverage samples;
- pseudonymous assessors, sessions, and presentations;
- randomized presentation schedules;
- canonical descriptor and dimension responses;
- a versioned multilingual question bank;
- calibration-mode and product-simulation assignments and responses;
- candidate-reference usefulness judgments;
- grouped split assignments; and
- analysis-run and release provenance.

Canonical descriptor references use foreign keys to active sensory attributes;
calibration observations do not change those concepts.

## Identity and condition fields

Where feasible, each real beverage sample records:

```text
study/protocol version
green coffee lot and public lot code
origin, variety, process, and storage notes
roast batch and roast date
measured roast color and measurement method
project seven-level roast category
preparation family, method, and recipe version
dose, water mass, beverage mass, grind metadata, brew time, water temperature
water composition, TDS, extraction yield
milk identity, milk proportion, beverage volume
serving timestamp, session, presentation order, repeat number
```

Missing scientific metadata must be represented explicitly and assessed against
the protocol tolerance. It must not be inferred from consumer-facing C0/C1.

## Observation cohorts

`reference_sensory` and `ordinary_user` are distinct cohorts. Reference
assessors provide repeated canonical descriptor and dimension observations.
Ordinary users provide consumer-readable question responses, familiarity,
confidence where approved, and candidate-reference usefulness judgments.

Expertise band is stored separately. Cohorts are not silently pooled.

## Question-bank records

Every language-specific question version records:

```text
question_id and stable question key
logical question code and version
language
question type and prompt
target distinction
eligible contexts
candidate-scope template
ordered answer options
minimum and maximum selected options
sensory modality
consumer familiarity requirement
evidence status and source note
lifecycle/readiness status
```

The assignment row freezes the actual candidate set before the question. This
keeps dynamic state out of the reusable question definition.

## Privacy contract

Public records use project-generated pseudonymous assessor keys. Public tables
must not contain names, email addresses, phone numbers, postal addresses,
account handles, or identity lookup keys. Any mapping from a person to a public
code remains outside the repository and public release.

Only analysis-justified broad metadata may be considered after ethical review,
such as expertise band, language, and broad experience category. Small-cell and
re-identification review is required before release.

## Consent and rights

Current gate values are:

```text
HUMAN_PARTICIPANT_ETHICS_REQUIRED=true
INSTITUTIONAL_APPROVAL_STATUS=NOT_OBTAINED
PUBLIC_DATA_CONSENT_REQUIRED=true
```

No recruitment or real human-observation collection is authorized by this
specification. A real release additionally requires approved consent covering
public redistribution, a completed rights review, and a passed PII scan.

## Split strategy

Before production model tuning, freeze development, validation, and held-out
test groups at the coffee-lot level. Repeated beverages, roast batches, and
nearly identical preparations derived from one lot stay in the same primary
split. Assessor-group holdouts are evaluated separately to test user
generalization.

The minimum pilot contains only two coffee lots and is a protocol-feasibility
study, not a production held-out benchmark. It must not be row-split to create
misleading performance. The preferred study supplies enough lots for grouped
development/validation/test partitions. Every frozen split records method,
seed, grouping variable, snapshot hash, and case inventory.

## Release package

```text
data/calibration/
  README.md
  DATA_DICTIONARY.md
  DATA_LICENSE.md
  CITATION.cff
  schema/
  templates/
  releases/
    protocol-and-schema-v0.1.0/
      manifest.json
      checksums.sha256
      data/
      protocol/
      analysis/
```

A future real release may use
`coffee-sensory-context-calibration-v0.1.0`. Until lawful real observations are
included, the package must use `protocol-and-schema-v0.1.0` and report zero
real observations.

Where practical, a real release will support PostgreSQL import, CSV, Parquet,
machine-readable schemas, deterministic analysis, frozen splits, a manifest,
checksums, source/rights metadata, and citation metadata. Large files must use
an appropriate release or archival mechanism rather than exceed GitHub limits.

## Quality gates

A releasable snapshot must pass:

- sample identity and condition linkage validation;
- current C0/C1 membership validation;
- seven-level roast coverage declared by the study design;
- protocol-version completeness;
- presentation and question-assignment uniqueness;
- response cardinality and eligibility checks;
- raw/derived/model claim separation;
- grouped split leakage checks;
- PII and small-cell review;
- rights and consent eligibility checks;
- manifest, checksum, license, and citation completeness; and
- two clean PostgreSQL rebuilds with matching logical inventories.

## Non-claims

This specification does not mean that preparation and roast predict flavor,
that a reference panel provides objective truth, that candidate scores are true
probabilities, or that a public calibration dataset has already been collected.
