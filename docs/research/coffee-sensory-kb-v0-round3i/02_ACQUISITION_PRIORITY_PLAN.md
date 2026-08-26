# Acquisition priority plan

## Decision basis

Round 3I starts from commit
`ccf5769cb5e1f165209e59beaef9fe54017265f5`. The expected-state target was
frozen before acquisition in `01_DATABASE_FREEZE_EXPECTED_STATE.md`. No
threshold may move because a source is difficult to acquire.

The acquisition order follows the failed hard gates:

1. independent contemporary tasting/evaluation language families;
2. at least 500 new source-authored sensory documents;
3. enough observed, de-duplicated expressions to reach 2,500 globally;
4. two independent source-authored Simplified-Chinese families;
5. a fourth cross-source association range only if defensible evidence is
   encountered.

Canonical concepts, active sensory attributes, model runs, embeddings,
participant collection, and product frontend files are outside this round.

## Count boundaries

- A language family is one canonical origin. Mirrors, repository copies,
  translations, and multiple files from one origin count once.
- A contemporary document must contain a source-authored sensory description
  or a source-local coffee evaluation record. Chemistry rows, preparation-only
  definitions, generic product titles, and surveys without sensory variables
  do not count.
- A normalized expression is counted once after NFKC, case folding, and
  Unicode-whitespace collapse. Artificial spelling variants and project or
  machine translations never count.
- Firstbloom is the historical language baseline. Its still-unsampled records
  can contribute new governed documents and expressions, but it cannot become
  a new independent family.
- Existing rights-cleared sensory sources may contribute a newly governed
  language-document surface when the source record itself contains sensory
  wording. This changes neither its origin identity nor its numeric outcome
  semantics.

## Target batches

### Batch 1 — contemporary research evaluation records

Promote source-local language documents from three already pinned independent
origins:

- Dryad Cotter black-coffee consumer evaluations, version 4, CC0-1.0: 3,186
  source rows containing sensory/JAR/CATA fields;
- Frontiers Figshare Bollen Robusta profiles, item 25735122 version 1, CC BY
  4.0: 95 source-local sample profiles;
- Vezzulli et al. Table 2, PMC8953325, CC BY 4.0: eight sample/preparation
  profiles reconstructed from 160 source medians.

These records qualify as coffee evaluation records, not prose corpora. Their
source-local scales and missingness remain intact. They are not pooled merely
because they share words.

### Batch 2 — Firstbloom long-tail expansion

Reprocess the complete pinned commit
`a6cb0026d1af9642724793c799bbc48dc189ba35` rather than resampling a live
catalog. The pinned `product_releases.csv` has 4,498 releases with non-empty
tasting-note fields; Round 2B captured 2,474. Only the remaining source release
identities are new documents.

Candidate phrases must pass a structural prose gate and two independent
Codex-assisted sensory-language review passes. Only consensus admissions may
be stored as text or count. The review is project curation, not human evidence,
automatic language detection, a canonical mapping, or an objective flavor
label.

### Batch 3 — source-authored Simplified Chinese

Admit only fixed, source-authored Chinese publications or datasets with an
explicit redistribution/derivative basis. Preserve the exact Chinese text,
source version, file hash, and expression role. English abstracts and project
translations do not qualify. If two independent families pass but fewer than
200 sensory expressions are available, retain the preferred-depth warning.

### Batch 4 — high-value evidence only

Admit additional sensory or relationship material only if it reduces source
concentration, adds a new context cell, or supplies defensible support or
challenge evidence. A fourth cross-source range is preferred, not required.

## Stop rule

After every batch, regenerate the language inventory and run the model-prebuild
readiness gate. Stop broad acquisition immediately when all hard gates pass.
If three consecutive targeted batches produce no gain in a failed hard
dimension, return `DATABASE_FREEZE_BLOCKED_BY_DATA_GAP` instead of lowering a
threshold.

## Public export boundary

Every admitted source receives separate decisions for raw text, derived
expressions, derived counts, and future model research. Public artifacts contain
only content permitted by the source license and the project's attribution
rules. Sanitized aggregate TSVs remain preferred where upstream files embed
local paths or author metadata.
