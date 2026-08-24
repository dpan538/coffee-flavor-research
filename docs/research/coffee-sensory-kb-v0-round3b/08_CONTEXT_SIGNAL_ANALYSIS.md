# Context signal analysis

Research question: do preparation, roast, or their interaction add measurable
information about sensory outcomes in the frozen Round 3B snapshot?

Input: 4,817 records from the two imported sources, separated by outcome type.
Assumption gate: a main effect requires at least two populated levels with
sensory outcomes; an interaction requires replicated crossed preparation ×
roast sensory cells. Output: sufficiency/identifiability decisions, not
coefficients. Limitation: the sensory and context variation occur in different
sources.

The 3,186 consumer sensory rows all use batch-filter preparation and the
project medium roast category, forming one crossed cell. The 1,631
meta-analysis rows supply preparation and roast variation but chemical, not
sensory, outcomes. Consequently:

- preparation signal: `NOT_ESTIMABLE`;
- roast signal: `NOT_ESTIMABLE`;
- preparation × roast interaction: `NOT_ESTIMABLE`.

No ANOVA, regression, permutation test, effect size, model-fit comparison, or
production flavor coefficient is reported because the necessary design is
absent. All three signal sufficiency flags are false. This is a successful
scientific abstention, not a negative finding that context has no effect.
