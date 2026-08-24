# Context schema audit

## Result

The new `context` schema is justified by claim type rather than aesthetics. Preparation, serving additions, roast labels, and roast measurements are contextual conditions. They remain outside:

- `kb` canonical sensory concepts;
- `corpus` raw language observations;
- `ml` candidates and inference;
- `audit` evaluations.

## Forward-only migration inventory

| Migration                          | Result                                                                        |
| ---------------------------------- | ----------------------------------------------------------------------------- |
| `018_context_schema.sql`           | normalized tables, controlled FKs, candidate keys, checks, indexes            |
| `019_context_integrity.sql`        | hierarchy, ambiguity, scheme, observation, addition, and measurement triggers |
| `020_context_taxonomy_seed.sql`    | deterministic sources, datasets, taxonomies, expressions, mappings, additions |
| `021_context_views_validation.sql` | five governed views and 23 validation queries                                 |

No migration `000`–`017` changed. `db/migration-baselines/round2b.sha256` now protects all 18 historical files in addition to the existing Round 1 and Round 2A manifests.

## Normalization

- Surrogate identities are primary keys; stable `*_key` values are alternate keys.
- Source-scheme categories depend on `(scheme, source category code)`.
- Ordinals are unique within schemes and prohibited for unordered terminology.
- Expressions depend on `(language, normalized text)`.
- Mapping rows depend on source and target identity and include direct provenance.
- One observation-context record is permitted per captured document.
- Repeating beverage additions and roast measurements are normalized child relations.
- Canonical relationships do not use JSONB.

## Integrity highlights

- Acyclic preparation polyhierarchy.
- Canonically ordered symmetric relations.
- Explicit lexical ambiguity rather than destructive uniqueness.
- One project roast normalization target.
- Known/unresolved/unknown/not-reported/not-applicable state consistency.
- Method-specific roast measurement bounds.
- `RESTRICT` update/delete policy for provenance history.
- No context sensory-score columns.

See [10_DATABASE_CONTEXT_MODEL.md](../../research/coffee-sensory-kb-v0-round3a/10_DATABASE_CONTEXT_MODEL.md) for relation-level detail.
