# Round 2A concept-scheme audit

Date: 2026-08-24

Status: scheme contract verified in two clean PostgreSQL 17 rebuilds

## Modeling decision

Source-specific organization is evidence, not universal ontology truth.
Migration `009_concept_schemes.sql` therefore places schemes, nodes, edges, and
reviewed mappings in the `evidence` schema. None is unioned into
`kb.concept_relation`, and canonical tables have no scheme ownership column or
foreign key.

The model permits one canonical concept to participate in multiple schemes,
permits multiple parents inside one scheme, rejects duplicate direct edges, and
uses a serialized recursive check to reject active direct or indirect cycles.
Every scheme is tied immutably to one `evidence.source_version` with restrictive
foreign keys.

## Seeded schemes

| Scheme key                                         | Rights posture                                            | Total nodes | Current nodes | Total mappings | Current mappings | Total edges | Active/candidate edges |
| -------------------------------------------------- | --------------------------------------------------------- | ----------: | ------------: | -------------: | ---------------: | ----------: | ---------------------: |
| `scheme.project.coffee_sensory_kb_v0.2026-08-24`   | Project-authored; production-exportable                   |         130 |           114 |            130 |              114 |         106 |                 98 / 8 |
| `scheme.wcr.sensory_lexicon_2_0.public_24_partial` | Personal-use/reuse-restricted; production export disabled |          24 |            24 |             15 |               15 |           0 |                  0 / 0 |

“Current” views include only active, in-validity-window schemes, nodes,
mappings, and edges. The project scheme retains all 16 candidate concepts as
candidate nodes/mappings for governance without publishing them through the
current projection. Seven candidate sensory concepts have eight candidate
placement edges because `sensory.green_tea` has two candidate parents;
`sensory.pink_grapefruit` is deliberately unplaced.

The WCR projection does not contain definitions, reference preparations,
intensities, the full 110-attribute vocabulary, or Flavor Wheel placement. Its
flat shape is intentional: Round 2A has no permission or scientific reason to
reproduce a protected hierarchy.

## Polyhierarchy fixture

Only the independently authored project V0 scheme demonstrates current multiple
parents. Its `metallic` node is directly organized under both the project
`chemical` and `taste_oral` categories. Candidate `green_tea` is stored under
both `green_herbal` and `tea`, but candidate edges are not returned by the
current hierarchy view. These are organizational projections, not universal
perceptual coordinates and not claims about WCR or SCA placement.

The semantic suite verifies that:

- the project fixture has two distinct parents;
- the current scheme graph remains acyclic;
- the WCR partial scheme has 24 nodes and zero edges;
- WCR mappings distinguish equivalence from association;
- all nine intentionally unmapped WCR nodes remain visible in
  `kb.v_scheme_projection`; and
- no `kb` table silently acquires scheme ownership or a source-scheme foreign
  key.

## Isolation controls

- Each scheme is tied immutably to one `evidence.source_version`.
- Composite foreign keys prevent edge endpoints or mapped nodes from crossing
  scheme boundaries.
- Duplicate direct edges are prohibited.
- A serialized recursive trigger rejects both direct and indirect active
  cycles.
- `evidence.v_current_scheme_hierarchy` and
  `evidence.v_current_scheme_concept_mapping` preserve source, version,
  licence, and production-export fields.
- `kb.v_scheme_projection` is node-complete, so an unmapped source node is
  visible rather than silently discarded.

Both clean rebuilds reproduced these scheme counts. The 47-check validation
contract reported zero scheme, cycle, mapping-cardinality, isolation, or rights
violations, and both direct and indirect cycle negative tests failed with the
expected named constraint.
