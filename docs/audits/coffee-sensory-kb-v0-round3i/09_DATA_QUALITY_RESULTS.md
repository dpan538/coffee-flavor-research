# Data-quality results

## Artifact-level checks

Static inspection of the generated Round 3I language artifacts returns zero for
all of these critical counts:

| Check                                                                         | Critical count |
| ----------------------------------------------------------------------------- | -------------: |
| Duplicate `(language_code, normalized_expression)` identities across Round 3I |              0 |
| Duplicate expression keys                                                     |              0 |
| Duplicate document keys                                                       |              0 |
| Duplicate occurrence keys                                                     |              0 |
| Occurrences without a generated document                                      |              0 |
| Occurrences without a generated expression                                    |              0 |
| Documents without a generated source                                          |              0 |
| Documents without a generated family                                          |              0 |
| Invalid document SHA-256 forms                                                |              0 |
| Counted machine-translated or artificial expressions                          |              0 |
| Machine-translated or artificial documents                                    |              0 |

The 20 baseline overlaps are explicit non-novel observations, not hidden
duplicates. Global countability de-duplicates them before reporting the 2,996
total.

## Governance completeness

All six admitted language-source rows have complete source identity, exact
version, rights, privacy, file-manifest hash, row-accounting, language,
geography, evidence-role, and limitation fields. The new relationship claim
resolves to an admitted Dryad snapshot and files with matching declared and
verified hashes. Together with the pre-existing governed registry, the intended
freeze-gate results are:

Row accounting uses the declared unit
`reviewed_candidate_sensory_occurrence_or_cell`; quality checks do not compare
those candidate counts directly with physical file rows or document counts.

- `SOURCE_ANNOTATION_COMPLETENESS=1.0000`
- `RIGHTS_REVIEW_COMPLETENESS=1.0000`
- `PRIVACY_REVIEW_COMPLETENESS=1.0000`
- `SOURCE_FILE_HASH_COMPLETENESS=1.0000`
- `RELATIONSHIP_PROVENANCE_COMPLETENESS=1.0000`

The executed freeze gate emits each value above as `1.0000` and passes all five
hard governance checks.

## Semantic and privacy checks

No missing value is converted to zero, and no CATA, JAR, liking, intensity,
descriptor-frequency, or prose field is collapsed into a shared scale. Eligible
feature rows preserve units, missingness, harmonization, and pooling status;
unresolved or incompatible rows are excluded from the approved feature view.

Cotter public artifacts omit pseudonymous evaluator linkage fields. Bollen and
Vezzulli use sanitized aggregates. Chinese artifacts retain public authorship
only and exclude comments, contact/security metadata, images, unrelated page
copy, and AI advice. No newly collected person or real-human validation record
exists.

Canonical counts remain 130 and 92; feature and partition counts remain 20 and 12. Seven declared future-split leakage controls remain passing, but no split or
model evaluation was executed.

Migration 048 makes the absence of model work executable rather than merely
documentary: it snapshots model-run, model-version, and embedding-configuration
counts and requires a `0/0/0` delta. The current audit also finds no ontology
change, no newly collected human-validation row, and no product-frontend change.
The external two-rebuild result remains a separate reproducibility attestation,
not a seeded quality claim.

| Final quality field   | State                                                  |
| --------------------- | ------------------------------------------------------ |
| Canonical freeze pass | true: 130 concepts; 92 active sensory                  |
| Schema integrity pass | true: zero orphans or unvalidated governed constraints |
| Data-quality pass     | true: zero critical violations                         |
| Leakage-audit pass    | true: zero failed controls                             |

The same execution reports `model_prebuild.data_ready=true`, a `0/0/0`
model-run/model-version/embedding delta, eight approved surfaces, complete
release membership, and 11 verified artifact hashes. The external two-rebuild
receipt now passes; the in-database gate still reports its intentionally
unseeded attestation row as informational until final release attestation. That
separation does not negate these database quality results.
