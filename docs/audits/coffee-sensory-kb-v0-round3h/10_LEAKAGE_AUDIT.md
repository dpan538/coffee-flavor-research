# Leakage audit

Leakage checks cover all 12 partitions and preserve source-family grouping.
Additional protected keys include coffee/sample identity, participant,
document, genotype and harvest, roast, preparation, milk mode, and panel type
where the source design requires them.

The audit rejects row-random future splitting and undeclared cross-partition
pooling. It passes as a prebuild governance check; no train/test split or model
evaluation was executed.
