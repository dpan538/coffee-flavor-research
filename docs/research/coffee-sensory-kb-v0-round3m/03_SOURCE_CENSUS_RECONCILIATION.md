# Source census reconciliation

## Exact Round 3L recomputation

`db/scripts/build-round3l-public-checkpoint.py` was rerun against the persistent
restricted freeze and its authoritative gate receipt. It reproduced:

| Surface                          |  Count |
| -------------------------------- | -----: |
| Census items                     |    480 |
| Editions                         |    267 |
| Artifacts                        |    848 |
| Parsed publication rows          | 26,531 |
| Staged publication rows          | 26,515 |
| Canonical publication rows       | 20,994 |
| Staged effective-core candidates |  6,754 |
| Staged assertions                | 11,801 |
| Staged gate-type candidates      |    376 |
| Reviewed descriptors             |      0 |
| Model-eligible descriptors       |      0 |

The regenerated public files were byte-identical to the checked-in generated
files; the checked-in directory additionally contains its explanatory README.

## Route versus family

The census contains 131 route/family keys. These are not 131 independent
training families. Round 3M preserves route, schema, edition, publication host,
organizer, rights lineage, mirror lineage, and independent source family as
separate concepts.

A conservative publication-origin grouping produces 11 families. All CoE
country and edition routes remain one ACE/CoE family. All WCC central and
competition-body routes remain one conservative WCC family until reviewed
independence evidence supports a finer split. This grouping prevents route and
host proliferation from passing diversity gates.

The complete 480-row audit is
`db/data/round3m/SOURCE_CENSUS_UNIVERSE.tsv`; route-level counts and
dispositions are in `SOURCE_ROUTE_DISPOSITION.tsv` and
`SOURCE_ROUTE_YIELD.tsv`.

The 131 route dispositions are 103 `EXCLUDED_LOW_YIELD`, 5
`PARTNERSHIP_ONLY`, 3 `PROVENANCE_PILOT_ONLY`, and 20 `UNRESOLVED_ROUTE`.
The census-item surface separately retains 1 `PRIORITY_DESCRIPTOR_ROUTE`, 24
provenance-pilot items, 3 existing-candidate review items, 9 partnership-only
items, 211 low-yield exclusions, and 232 unresolved items. No discovered item
is erased by a rights or access blocker.
