# 04 — Semantic Smoke Tests

- Receipt date: 2026-08-24
- Suites: `db/tests/semantic.sql`, `db/tests/retrieval.sql`

Relational validity is not sufficient for this model. These read-only tests
assert the meanings that must survive schema implementation.

| case                      | observed result                                                                                                                                                       | result |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| Pink grapefruit           | Own active `sensory.pink_grapefruit` identity and preferred expression; grapefruit is broader; no collapse to `sensory.grapefruit`.                                   | PASS   |
| Earl Grey                 | Resolves to active `composite.earl_grey`; expands via `consumer_reference_for` to bergamot and `composite_has_component` to black tea; never lexicalizes as bergamot. | PASS   |
| Bright                    | `qualifier.bright`, lifecycle `candidate`; no concept intensity/score/weight/acidity column and no projection value.                                                  | PASS   |
| Tea-like                  | Candidate qualifier distinct from active `sensory.black_tea`.                                                                                                         | PASS   |
| Meteor fruit              | Active expression exists, has no active canonical lexicalization, appears as `UNRESOLVED`, and exact retrieval does not fall through to a nearby spelling.            | PASS   |
| Fermented                 | `sensory.fermented_character` resolves from “fermented” and remains distinct from `process.fermentation`.                                                             | PASS   |
| Winey                     | One expression retains two explicit mappings: qualifier and sensory interpretation. Candidate concepts are not exposed as current canonical resolutions.              | PASS   |
| Rights gate               | Public pink-grapefruit observation is distributable; restricted meteor-fruit observation/text is absent.                                                              | PASS   |
| Language extensibility    | `zh-Hans` is a controlled language tag without inventing Chinese seed assertions.                                                                                     | PASS   |
| Numeric evidence boundary | Seed has zero pair measurements, calibrations, co-occurrence measurements, or candidate signals.                                                                      | PASS   |
| pgvector gate             | No installed `vector` extension; retrieval uses `pg_trgm`.                                                                                                            | PASS   |

## Retrieval ordering observed

1. `grapefruit` returned `EXACT_PREFERRED_LABEL` and typed graph expansion.
2. `pink-grapefruit` returned `EXACT_APPROVED_VARIANT`.
3. Misspelled `grapfruit` returned lexical `TRIGRAM` matches; grapefruit's
   similarity was approximately `0.61538464`. This number is spelling
   similarity, not sensory distance.
4. `Earl Grey` returned its exact composite plus two typed graph rows.
5. Exact-unmapped `meteor fruit` returned exactly one `UNRESOLVED` row with no
   concept or score.

The lawful fixture contains exactly 19 concepts, 23 expressions, 23 active
lexicalizations, five active typed relations, and six sample-level sensory
dimensions. It is not the planned production ontology.

```text
SEED_CONCEPT_COUNT=19
UNRESOLVED_TEST=true
RESTRICTED_TEXT_EXPORT_PASS=true
SEMANTIC_SMOKE_PASS=true
TRIGRAM_RETRIEVAL_PASS=true
```
