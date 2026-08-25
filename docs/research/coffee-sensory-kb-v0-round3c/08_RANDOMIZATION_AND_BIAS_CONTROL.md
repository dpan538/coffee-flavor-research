# Randomization and bias control

The unit of randomization is the presentation, constrained within cohort, session, and sample coverage. A reproducible cryptographic seed identifies each generated schedule; schedules are frozen before serving and stored separately from observation entry.

## Controls

- balanced incomplete blocks limit fatigue while spreading conditions across assessors;
- presentation codes conceal coffee, roast, preparation, and expected descriptors;
- Latin-square or Williams-style order balancing controls first-order carryover where feasible;
- black/milk pairs are separated unless the registered contrast explicitly requires adjacency;
- preparation operators do not score their own samples in the reference cohort;
- question options and candidate cards are position-randomized;
- repeated samples use different presentation codes;
- assessors cannot see consensus, model output, roaster copy, or prior responses;
- withdrawals and missingness are retained with reason codes.

Duplicate `(session, sequence_position)` and duplicate `(session, beverage_sample)` assignments are database errors. A schedule-generation log records algorithm, seed, input manifest hash, constraints, retries, and output hash.

## Leakage prevention

Model splits are grouped by coffee lot and keep replicate beverages, roast batches, and nearly identical preparations together. Assessor identities are also isolated where an assessor-generalization analysis is claimed. Random row splits are prohibited. Minimum-pilot data cannot support a defensible three-way lot split because it contains only two lots; split-performance claims therefore remain `NOT_ESTIMABLE` at that scale.
