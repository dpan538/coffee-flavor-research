# Deterministic ranking engine

The engine implements `C0 required → C1 seven levels required → Q1–Q4 →
exceptional Q5 → five primary + three secondary`. It uses two auditable stages:
individual candidate generation from the 24 public pilot descriptors, followed
by constrained greedy set selection under objective `M(S|x)`.

Context is a soft prior. Direct answers receive sufficient weight to override a
weak preparation/roast prior, and every override is recorded. The receipt keeps
individual, context, answer, source, professional, ontology, community,
outlier, redundancy, and direct-evidence components rather than only a final
score.

Evidence is described as stronger, moderate, weaker, secondary, or
insufficient. No probability is emitted. If eight non-redundant supported
candidates are unavailable, the engine abstains rather than adding filler.
