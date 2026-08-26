# Current-view contract

## Contract

Future model-prebuild work must begin from the eight views registered as
`CURRENT_APPROVED` for `coffee-sensory-research-db-v0.1.0`. Their SQL
definitions are hashed in the release registry. They are read surfaces, not a
training split, a pooled score table, or permission to bypass source rights.

| Role                   | Approved database object                    | Superseded research surface                      | Inclusion boundary                                                                                                                                 |
| ---------------------- | ------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Canonical concept      | `kb.v_current_canonical_concept`            | `kb.v_current_canonical_ontology`                | Delegates to the frozen 130-concept ontology; Round 3I adds no concept.                                                                            |
| Lexical evidence       | `kb.v_current_lexical_evidence`             | `kb.v_lexical_resolution`                        | Joins governed observed language to lexical resolutions without forcing unresolved expressions into concepts.                                      |
| Context                | `context.v_current_context`                 | `audit.v_model_prebuild_context_coverage`        | Includes admitted, observed, source-local, non-zero-filled context cells only.                                                                     |
| Sensory partition      | `evidence.v_current_sensory_partition`      | `evidence.v_model_prebuild_source_partitions`    | Includes only partitions marked `ELIGIBLE_AFTER_FUTURE_PROTOCOL`; it does not create a train/test split.                                           |
| Language corpus        | `corpus.v_current_language_corpus`          | `corpus.v_model_prebuild_language_inventory`     | Combines the frozen Round 2B normalized baseline with release-member Round 3I occurrences that pass source, rights, lifecycle, and review filters. |
| Relationship evidence  | `evidence.v_current_relationship_evidence`  | `audit.v_model_prebuild_relationship_delta`      | Includes reviewed `SUPPORTS`, `CHALLENGES`, and `MIXED` claims whose source and snapshot are admitted.                                             |
| Question evidence      | `calibration.v_current_question_evidence`   | `calibration.v_model_prebuild_question_evidence` | Includes research-supported question targets whose supporting families all remain admitted.                                                        |
| Model-prebuild feature | `evidence.v_current_model_prebuild_feature` | `evidence.v_model_prebuild_feature_availability` | Includes `PREBUILD_ONLY` definitions and partition features with resolved, compatible harmonization on eligible partitions.                        |

## Language-view semantics

`corpus.v_current_language_corpus` is occurrence-grained. Multiple documents
may therefore expose the same normalized expression. A consumer computing the
global vocabulary must use the governed count flag and de-duplicate by
`(language_code, normalized_expression)`; it must not count view rows as unique
expressions.

The view exposes raw source phrases only where both the document and source
permit raw redistribution. Otherwise the hash, normalized expression,
provenance, and limitation remain available without leaking denied raw text.
Rejected, quarantined, deprecated, unreviewed, rights-blocked, machine-
translated, and artificial-variant rows are outside the approved surface.

The global count is 2,996: the 1,777-entry migrated baseline plus 1,219 new
identities. The Round 3I expression artifacts contain 1,239 rows because 19
evaluation expressions and one Firstbloom expression overlap the governed
baseline. Those observations remain traceable but contribute zero novelty.

## Evidence-view semantics

The relationship view is deliberately narrower than the frozen claim table.
`INSUFFICIENT` and `OUT_OF_SCOPE` claims remain preserved in the database for
audit and contradiction history but are not exposed as positive future
prebuild evidence. `CHALLENGES` and `MIXED` remain visible; freeze does not
silence contradictory evidence.

The question view expresses independent research support only. It does not
assert user validation or information gain: both counts remain zero. The
feature and partition views preserve source-local units, missingness,
harmonization, and pooling decisions; view membership does not make values
cross-source comparable.

## Historical surfaces

The following eight objects remain queryable for historical reproducibility
but are registered as `DEPRECATED_RESEARCH`, not approved future prebuild
entrypoints:

- `kb.v_current_canonical_ontology`
- `kb.v_lexical_resolution`
- `audit.v_model_prebuild_context_coverage`
- `evidence.v_model_prebuild_source_partitions`
- `corpus.v_model_prebuild_language_inventory`
- `audit.v_model_prebuild_relationship_delta`
- `calibration.v_model_prebuild_question_evidence`
- `evidence.v_model_prebuild_feature_availability`

Deprecation does not delete a historical migration or invalidate an earlier
audit. It removes ambiguity about which surface a new consumer should use.

## Mutation rule

Before final attestation, the view definitions may change only through the
candidate's forward migrations and must receive new definition hashes. After
the release is attested on exact main, event triggers reject altering,
replacing, or dropping an approved view. Future changes require a new migration,
new definitions and hashes, a new manifest, and a new release version.
