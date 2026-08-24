# Preparation normalization

The resolver preserves a layered distinction:

```text
raw familiar expression
→ reviewed lexical rule
→ preparation leaf when safely specific
→ one of eight C0 families
```

Examples include V60 and pour-over terms under filter/percolation, French
press under immersion, espresso under espresso/short pressure, Americano and
long black under espresso + water, cold brew under cold extraction, and latte,
flat white, and cappuccino under espresso + milk. AeroPress retains its
polyhierarchical internal identity while the candidate user wording avoids
requiring an ordinary user to settle an academic classification.

The current production-safe view exposes exactly eight families with candidate
English and Simplified Chinese labels. It contains no observation-status
value. A database trigger rejects any attempt to introduce an unknown-like
top-level C0 family.

Held-out C0 results are: 9 cases, family coverage 1.0000, leaf coverage 0.8889,
Recall@1 family 1.0000, Recall@1 leaf 1.0000 among cases with an expected leaf,
ambiguous rate 0.0000, unresolved rate 0.0000, and gross-family error 0.0000.
These project-authored lexical cases establish a deterministic regression
baseline, not independent evidence that ordinary users understand every label;
`C0_NORMALIZATION_DATA_SUFFICIENT=false`.
