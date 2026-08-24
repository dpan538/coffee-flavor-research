# Database context model

## Why a `context` schema is justified

Preparation and roast are neither canonical sensory knowledge nor raw industry language. They are experimental, production, and serving conditions that can be reported, normalized, measured, unknown, or unresolved. Placing them in `kb` would contaminate concept typing; placing them in `corpus` would make a particular observation store own the taxonomy; placing them in `ml` would make stable context depend on inference.

The dedicated schema therefore represents a distinct scientific boundary:

```text
kb canonical sensory identity
≠ context preparation/roast condition
≠ corpus observed language
≠ ml inference
≠ audit evaluation
```

## Relations

### Preparation

- `context.preparation_concept`: stable family, method, and beverage-style identities.
- `context.preparation_relation`: typed broader and related edges with direct source version, role, and locator.
- `context.preparation_concept_support`: many-to-many support from preparation identity to immutable source version.
- `context.preparation_expression`: language-tagged surface identity.
- `context.preparation_expression_mapping`: expression-to-concept mapping with certainty and provenance.

### Roast

- `context.roast_scheme`: project, source ordinal, or industry terminology scheme.
- `context.roast_category`: category local to one scheme; ordinal position is nullable and prohibited for unordered terminology schemes.
- `context.roast_category_mapping`: cautious source-category to project-target mapping.
- `context.roast_expression` and `context.roast_expression_mapping`: lexical layer with unresolved and polysemous behavior.
- `context.roast_measurement_method`: method, basis, bounds, direction, and source version.

### Observation context

- `context.observation_context`: one contextual record per captured document, with separate reported and normalized preparation/roast fields.
- `context.observation_addition`: many additions per observation context.
- `context.observation_roast_measurement`: method-specific numeric values with source provenance.
- `context.beverage_addition_type`: extensible addition hierarchy with explicit strong-interference flag.

The Round 2B snapshot receives no context rows because its structured source files do not report these fields.

## Keys and dependencies

All base entities use identity primary keys plus stable text candidate keys declared `UNIQUE NOT NULL`. Representative functional dependencies are:

```text
preparation_concept_key → type, lifecycle, label, description, C0 flags
(language_tag, normalized_text) → preparation_expression_id
roast_scheme_key → kind, lifecycle, source_version, target flag
(roast_scheme_id, source_category_code) → roast_category_id
(roast_scheme_id, ordinal_position) → roast_category_id, when ordinal is present
captured_document_id → observation_context_id
(observation_context_id, roast_measurement_method_id) → measured value
```

These determinants are candidate keys; descriptive attributes do not determine identity. The design is in 3NF and the small controlled-code tables are in BCNF.

## Foreign-key policy

Every foreign key uses `ON UPDATE RESTRICT ON DELETE RESTRICT`. Historical source versions, context supports, mappings, corpus documents, and measurements cannot be silently deleted or retargeted. Lifecycle state and forward migrations handle change.

## Checks and triggers

- broader preparation hierarchy rejects self edges and cycles;
- symmetric `related_to` edges have canonical endpoint ordering;
- competing current expression senses are allowed only when every mapping is explicitly ambiguous;
- ordinal schemes require positions; terminology schemes prohibit them;
- roast normalization targets must belong to the one explicit project target scheme;
- `known` observation states require a normalized value;
- `reported_unresolved` requires a source expression and prohibits a normalized target;
- unknown/not-reported/not-applicable prohibit invented targets;
- normalized roast observation values must use the project target scheme;
- addition rows require `present` status;
- measured roast values must fall within method bounds;
- addition hierarchy rejects cycles.

## Provenance closure

External and project assertions point directly to `evidence.source_version`. A version has a mandatory licence policy. Preparation supports distinguish project authorship, empirical observation, source reporting, interpretation, corroboration, and lexical mapping. Roast mapping rows carry the same closure directly.

## Views

- `context.v_preparation_taxonomy`: parents, children, and support counts.
- `context.v_roast_normalization`: source-scheme-complete mapping projection.
- `context.v_observation_context`: reported and normalized values plus addition counts.
- `context.v_unresolved_context_labels`: explicit abstention queue.
- `context.v_context_coverage`: deterministic Round 3A count receipt.

## Separation from numeric sensory semantics

No context table contains a sensory score, flavor probability, or sensory weight. Roast ordinal positions are ordering metadata. Measurement values are physical/instrument-method observations and are not connected to `kb.concept` intensity.

## Forward migrations

| Migration                          | Purpose                                                                                  |
| ---------------------------------- | ---------------------------------------------------------------------------------------- |
| `018_context_schema.sql`           | normalized tables, reference domains, keys, FKs, checks, indexes                         |
| `019_context_integrity.sql`        | cycle, ambiguity, scheme-isolation, observation, addition, and measurement triggers      |
| `020_context_taxonomy_seed.sql`    | rights/source metadata, preparation/roast taxonomies, lexical layer, datasets, additions |
| `021_context_views_validation.sql` | governed views and machine-runnable validation contract                                  |

Migrations `000`–`017` are unchanged. A new Round 2B hash manifest makes their immutability machine-verifiable.
