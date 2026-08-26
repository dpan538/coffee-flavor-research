# Negative tests

`db/tests/round3i_negative.sql` defines 35 Round 3I rejection tests plus a
current-surface exclusion assertion. They extend, rather than replace, the
Round 3H model, embedding, canonical-freeze, partition, leakage, rights, and
hash tests executed at the immutable `000`--`044` checkpoint.

| Test                                         | Rejected condition                                                  |
| -------------------------------------------- | ------------------------------------------------------------------- |
| `mirror_counted_independent`                 | A mirror is counted as an independent family.                       |
| `duplicate_independent_origin`               | One canonical origin is split into another independent family.      |
| `project_authored_zh_translation_counted`    | Project-authored Chinese translation is counted as source evidence. |
| `machine_translated_document_counted`        | Machine translation is counted as observed `zh-Hans`.               |
| `artificial_expression_counted`              | An artificial variant enters the governed total.                    |
| `duplicate_normalized_expression_counted`    | A duplicate language/normalized-expression identity is counted.     |
| `preparation_expression_counted`             | Preparation vocabulary games the sensory-expression gate.           |
| `zh_roast_expression_counted`                | Roast vocabulary games the Chinese sensory count.                   |
| `rights_review_omitted`                      | An admitted source lacks completed rights review.                   |
| `manifest_hash_omitted`                      | A source manifest item lacks a valid SHA-256.                       |
| `raw_public_redistribution_denied`           | A document exports raw text beyond source rights.                   |
| `raw_internal_retention_denied`              | An occurrence retains raw text when internal use is denied.         |
| `candidate_hash_missing`                     | A review candidate has an invalid hash-bound identity.              |
| `candidate_text_retained`                    | The text-free candidate registry stores candidate text.             |
| `review_missing_candidate`                   | A review decision has no governed candidate.                        |
| `same_reviewer_both_passes`                  | One reviewer supplies both independent passes.                      |
| `dual_review_consensus_spoof`                | An expression claims dual consensus after a rejecting pass.         |
| `generic_document_gamed_as_sensory`          | A generic document is counted without sensory verification.         |
| `artifact_hash_mismatch`                     | Registered and verified artifact hashes differ.                     |
| `current_surface_role_spoof`                 | An object is assigned the wrong approved surface role.              |
| `deprecated_surface_approved`                | A deprecated surface is approved for future prebuild use.           |
| `threshold_lowered_without_approval`         | A frozen threshold is lowered without explicit governance approval. |
| `freeze_without_attestation`                 | A candidate is directly updated to `FROZEN`.                        |
| `frozen_document_mutation`                   | A frozen source document is changed in place.                       |
| `failed_mandatory_language_gate`             | A release proceeds after a mandatory language gate is made false.   |
| `missing_source_version`                     | A governed source loses its exact version.                          |
| `orphan_relationship_evidence`               | A relationship claim is disconnected from its source.               |
| `canonical_change_after_prebuild_checkpoint` | A new canonical concept is inserted after the checkpoint.           |
| `model_run_after_research_database_freeze`   | A prohibited model run is created from the prebuild state.          |
| `embedding_after_research_database_freeze`   | A prohibited embedding artifact is created.                         |
| `frontend_change_claim`                      | The execution guard falsely records a product-frontend change.      |
| `freeze_manifest_overwrite`                  | A registered freeze-manifest hash is overwritten.                   |
| `same_version_different_manifest_sha`        | One release version is rebound to a different manifest.             |
| `attestation_without_two_rebuild_evidence`   | Final attestation is attempted without an external rebuild receipt. |
| `future_frozen_member_in_place_mutation`     | A release member is changed after simulated attestation.            |

The additional assertion verifies that current language, relationship, and
sensory-partition views exclude rejected, quarantined, deprecated, unreviewed,
non-current, or ineligible rows.

The combined suite also relies on earlier guards to reject model/embedding
execution, false readiness, canonical drift, unsafe pooling, undeclared
missingness, split leakage, and source-hash violations before Round 3I is
applied.

| Receipt                          | State                                                           |
| -------------------------------- | --------------------------------------------------------------- |
| New Round 3I negative-test count | 35                                                              |
| Required minimum                 | 15                                                              |
| Local core execution             | pass: 33/33 before the two explicit closure fixtures were added |
| Final 35-test execution          | Not yet run; exact-candidate PostgreSQL 17 CI receipt required  |
| Constraint-test pass             | true for local core; final 35/35 external binding required      |

The last complete local PostgreSQL 17 execution ends with
`ROUND3I_NEGATIVE_TEST_COUNT=33`, `ROUND3I_NEGATIVE_TEST_PASS=true`, and
`DATABASE_TEST_PASS=true`. The final source now emits
`ROUND3I_NEGATIVE_TEST_COUNT=35`; the two added language-countability fixtures
must be confirmed by the exact-candidate remote PostgreSQL 17 job before the
final constraint receipt is externally bound.

The focused 214-line negative-test log at
`/private/tmp/round3i-negative-only-3.log` has SHA-256
`ccfc69df2f6c402ce89b9f32b67b59af80b6b9c6c04974f79ba12974d0da9692`.
