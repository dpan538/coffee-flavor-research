# Federated source partitions

The model-prebuild manifest declares 12 partitions: four baseline families,
five Round 3H outcome families, and three metadata-only instrument families.
Grouping keys preserve source family and, where applicable, coffee identity,
participant, document, genotype, harvest, roast, preparation, milk mode, and
panel type.

Eligible partitions are only `ELIGIBLE_AFTER_FUTURE_PROTOCOL`; none authorizes
current model use. The FT-NIR partition is ineligible and instrument-only
partitions are metadata-only. Incompatible response scales cannot be pooled
merely because they share a descriptor label.
