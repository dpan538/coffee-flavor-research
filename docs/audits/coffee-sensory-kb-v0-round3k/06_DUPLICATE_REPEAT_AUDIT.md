# Duplicate and repeat audit

## Governed distinctions

The schema distinguishes a legitimate repeat from a duplicate or mirror:

- a coffee served in preliminary, semifinal, and final rounds may yield separate
  round-service records only when entry, coffee identity, parent service, repeat
  code, and round lineage are explicit;
- the same entry in another category requires a governed relationship rather
  than an inferred new coffee;
- mirrored pages and republished auction/roaster material retain upstream source
  family and duplicate-group lineage;
- judge observations, scores, descriptors, files, and page captures are child
  evidence and never independent coffee records.

Duplicate groups require a valid group type and sufficient membership. Mirror
groups require one canonical member and linked upstream origin. Repeat audits
check identity and sequence consistency. Deterministic split groups keep coffee
identities, lots, duplicate groups, mirrors, and repeat groups together.

## Current audit state

No acquired service exists, so there is no observed duplicate group, repeat
relationship, or split assignment to audit. `UNLINKED_REPEAT_COUNT` is not
evaluated, and cross-split coffee, duplicate, and mirror leak counts are
vacuous zeros rather than passes.

Negative fixtures target unlinked final rounds, invalid one-member duplicate
groups, malformed mirrors, cross-service duplicate membership, repeat identity
breaks, and cross-split leakage. Native PostgreSQL 17 passes 9 core named
constraint failures, 32 integrated named failures, and 10 gate detection
assertions. The integrated leak fixture proves that a cross-split coffee identity
is both surfaced by the leakage view and rejected by the validation contract;
all fixtures roll back.
