# Global data-quality review

## Review scope

The quality boundary includes the pre-existing canonical, sensory, context,
relationship, question, feature, and partition registries plus every Round 3I
language and relationship artifact. A passing artifact review does not replace
database execution: all critical database counts must also be zero after the
clean rebuild used for the freeze manifest.

## Round 3I artifact reconciliation

| Plane                    | Materialized delta | Governed interpretation                                                                                                                    |
| ------------------------ | -----------------: | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Language documents       |              4,137 | 3,289 qualify for the new-contemporary gate; 840 Firstbloom and eight `zh-Hans` documents remain governed under different count decisions. |
| Expression artifact rows |              1,239 | 1,219 are globally new after the complete 1,777-entry baseline is reconciled.                                                              |
| Expression occurrences   |             12,755 | Occurrence frequency is not sensory prevalence or an independent sample count.                                                             |
| Relationship claims      |                  1 | One reviewed, non-causal Cotter acidity--citrus `SUPPORTS` claim; no lifecycle promotion.                                                  |
| Sensory outcome rows     |                  0 | The frozen total remains 4,344; existing source values are not re-imported as language rows.                                               |

The exact novelty equation is `1,777 + 18 + 952 + 249 = 2,996`.
Evaluation contributes 37 expression rows but only 18 new identities after 19
baseline overlaps. Firstbloom contributes 953 expression rows but only 952 new
identities after the `musty` overlap. The 249 source-authored `zh-Hans`
identities are new.

## Artifact-level critical checks

Static inspection of the generated TSV set produced these critical results:

| Check                                                                  | Critical count | Decision |
| ---------------------------------------------------------------------- | -------------: | -------- |
| Duplicate Round 3I `(language_code, normalized_expression)` identities |              0 | Pass     |
| Duplicate language expression keys                                     |              0 | Pass     |
| Duplicate language document keys                                       |              0 | Pass     |
| Duplicate language occurrence keys                                     |              0 | Pass     |
| Occurrences with no generated document                                 |              0 | Pass     |
| Occurrences with no generated expression                               |              0 | Pass     |
| Documents with no generated source                                     |              0 | Pass     |
| Documents with no generated family                                     |              0 | Pass     |
| Document content hashes with invalid SHA-256 form                      |              0 | Pass     |
| Counted machine-translated or artificial expressions                   |              0 | Pass     |
| Machine-translated or artificial document rows                         |              0 | Pass     |

All six admitted language-source annotations contain a non-empty exact version,
completed rights review, completed privacy review, a complete file-hash
decision, a complete annotation, and an admitted state. This is a field-
completeness statement, not permission to republish a whole source. Public
output remains bounded by each source's separate raw, expression, and count
decisions.

## Database-level critical checks

The freeze rebuild must report zero for each of the following before
`DATA_QUALITY_PASS=true` is allowed:

- duplicate primary or candidate identities;
- orphan family, source, document, expression, occurrence, relationship,
  question, feature, partition, release-member, surface, or artifact-hash rows;
- admitted sources missing title, owner, exact version, stable locator, rights
  basis, privacy decision, file manifest, or verified hash;
- hash mismatches or malformed SHA-256 values;
- admitted values with an undeclared unit, missingness semantic, harmonization
  state, or pooling decision;
- invalid admitted/lifecycle combinations;
- exposed direct identifiers or raw text beyond its source permission;
- canonical count drift from 130 concepts or 92 active sensory attributes;
- feature or partition drift from 20 and 12;
- a model, embedding, pgvector, real-human, frontend, or canonical-mutation
  execution flag; and
- a release member, manifest, artifact hash, or current view whose recomputed
  hash differs from its registered value.

## PII, units, and missingness

The public Cotter relationship derivative contains 27 brew-condition
aggregates, not the source's pseudonymous `Judge` field. Cotter language rows
are deidentified and exported as derived content only. The two Chinese sources
retain public authorship but exclude comments, contact/security metadata,
avatars, and unrelated page material. No Round 3I artifact contains a newly
collected person or a claim of real-human validation.

Round 3I performs no unit conversion or scale pooling. CATA flags, JAR adequacy,
trained-panel medians, descriptor frequencies, and source-authored prose remain
distinct. Existing feature definitions keep explicit units, missingness
semantics, harmonization states, and pooling permissions; incompatible or
unresolved features are excluded from the approved feature surface rather than
silently imputed.

## Leakage and concentration

The seven Round 3H future-split risks remain governed: same coffee, same
participant, duplicate product page, mirrored source, raw/derived overlap,
translation variant, and context derivative. Round 3I adds no split and cannot
therefore claim empirical leakage performance. Firstbloom retains one canonical
origin, and the language and relationship aliases of Cotter remain one Dryad
origin.

Source concentration remains a known limitation. In particular, 3,186 Cotter
consumer rows account for most new evaluation-language documents. The gate is
about governed coverage, not balanced sampling, and the current surfaces
preserve source keys so future work can stratify rather than mistake row volume
for source diversity.

## Release decision boundary

Artifact-level critical checks pass. The global result becomes
`DATA_QUALITY_PASS=true` only when the database-level checks, all 11 registered
hashes, the negative suite, and both clean rebuilds pass on the exact freeze
candidate. The audit package records that executable result; this research
review does not pre-empt it.
