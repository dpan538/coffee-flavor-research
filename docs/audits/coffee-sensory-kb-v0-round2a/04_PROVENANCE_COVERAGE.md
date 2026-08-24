# Round 2A provenance coverage

Date: 2026-08-24

Status: `PROVENANCE_CLOSURE_PASS=true`

## Schema sufficiency audit

Round 1 already had `evidence.concept_support`, but its support meaning was not
controlled. Migration `008_concept_provenance.sql` adds the normalized
`ref.concept_support_role` vocabulary and makes a role mandatory for every
concept-support assertion. It also creates
`evidence.v_concept_provenance`, which resolves each support row through its
source version, source, licence policy, rights status, and production-export
decision.

The nine roles are `legacy_unspecified`, `project_authorship`,
`lexicon_inclusion`, `reported_usage`, `empirical_observation`, `scope_basis`,
`regional_extension`, `interpretive`, and `corroboration`. Migration `010`
reclassifies inherited smoke rows as `project_authorship`; the frozen seed
requires `legacy_unspecified=0`.

This answers the core questions without storing copied definitions:

- “Who authored this concept scope?” is represented by
  `project_authorship` against a fixed project source version.
- “Which external source supported admission or scope?” is represented by a
  separate controlled-role support row and locator.
- “Which source-local vocabulary contains or organizes a label?” is represented
  independently by a versioned concept scheme and reviewed mapping.
- A project interpretation can be marked `interpretive`; none is inferred from
  old notes automatically.

## Frozen support inventory

The rebuilt database contains 244 concept-support rows. Both builds reproduced
the counts below.

| Support role               |    Rows |
| -------------------------- | ------: |
| `project_authorship`       |     149 |
| `lexicon_inclusion`        |      53 |
| `reported_usage`           |      17 |
| `scope_basis`              |      25 |
| `legacy_unspecified`       |       0 |
| All other controlled roles |       0 |
| **Total**                  | **244** |

The 149 project-authorship rows comprise 130 Round 2A concept scopes plus 19
historical Round 1 smoke-source records. Every one of the 130 concepts has a
Round 2A project-authorship support row, including externally admitted active
attributes: source evidence supports admission, while the project remains the
author of the canonical scope and description.

## External admission routes

The seed routes 92 active sensory attributes to at least one controlled-role
external support record. `sensory.pink_grapefruit` has one external
`scope_basis` row that explicitly supports only the broader grapefruit scope,
not activation of the narrower candidate. The other seven sensory candidates
have project-authorship support only.

| Source version              | Concept-support rows | Use in the support matrix                                                                                   |
| --------------------------- | -------------------: | ----------------------------------------------------------------------------------------------------------- |
| Chambers et al. (2016)      |                   54 | 52 active routed inclusions, pink-grapefruit broader scope, and an additional fermented-character inclusion |
| Williams et al. (2023)      |                    9 | Mouthfeel scope basis                                                                                       |
| Carvalho et al. (2025)      |                   12 | Reported usage                                                                                              |
| Ledezma et al. (2025)       |                    3 | Reported usage under a rights-unknown, metadata-only policy                                                 |
| Seninde and Chambers (2020) |                    5 | Cross-source scope basis                                                                                    |
| Zhang et al. (2019)         |                    2 | Processing-context scope basis only, not direct sensory-term reporting                                      |
| Muenchow et al. (2020)      |                    6 | Roast and brown-note scope basis                                                                            |
| Batali et al. (2022)        |                    1 | Reported usage                                                                                              |
| Bollen et al. (2024)        |                    2 | One reported-use and one scope-basis route                                                                  |
| WCR Lexicon 2.0 public page |                    1 | “Acetic acid” as non-equivalent scope basis for project-authored `sensory.acetic_vinegar`                   |
| SCA CVA and ISO 18794:2025  |                    0 | Governance/method metadata only; no canonical admission assertion                                           |

The two Zhang-supported concepts have additional conservative context where
needed: Chambers records lexicon inclusion for fermented character, and the WCR
public-page label “Acetic acid” is only a broader/non-equivalent scope basis for
`sensory.acetic_vinegar`. No source definition or hierarchy is imported.

## Lexicalization and relation provenance

All 134 canonical lexicalizations are independently project-authored, even
when their concepts have external admission support. The frozen support set has
157 lexicalization-support rows: 134 against the Round 2A project source and 23
historical Round 1 project-smoke supports. There are zero externally scoped
lexicalizations; this prevents a project label from being misrepresented as
source wording.

Canonical relations are also project-authored. Their support rows identify the
project source and explicitly disclaim universal hierarchy, source placement,
and inferred transitive closure. The validation gate covers every active
relation whose relation type requires evidence, not only relations marked
external.

## Closure gates

| Required gate                                                          | Runtime result |
| ---------------------------------------------------------------------- | -------------: |
| Concepts with at least one resolved provenance row                     |            130 |
| Concepts without provenance                                            |              0 |
| Active externally sourced concepts without versioned provenance        |              0 |
| Active externally sourced lexicalizations without versioned provenance |              0 |
| Active relations without required versioned provenance                 |              0 |
| Concept-support rows without resolved source/version/licence           |              0 |
| Legacy-unspecified concept-support rows                                |              0 |

`audit.run_round2a_validation_queries()` reported zero violations for every
provenance check in both clean rebuilds.

## Historical deletion safety

Sources and source versions referenced by support or scheme rows use
`ON DELETE RESTRICT`. Round 2A negative tests attempt source deletion,
source-version deletion, and scheme source-version mutation and require the
named foreign-key/check failures. Historical provenance is retained rather
than silently cascaded away.
