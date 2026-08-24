# Seven-level roast normalization

`roast.scheme.project_v1_seven_level` supersedes the historical V0 interaction
scheme and exposes seven active ordered categories. The V0 scheme and its five
categories remain present, immutable, deprecated, and non-current. Explicit
V0→V1 mappings preserve provenance without renaming old stable keys.

The mapping layer accepts compatible qualitative forms, including English and
Simplified Chinese lexical variants, while preserving abstention for unstable
trade/style or brew-intent terms. `filter roast`, `espresso roast`,
`omniroast`, `Nordic roast`, `City roast`, `City+`, `Full City`, `Vienna`,
`French`, and `Italian` do not acquire a project darkness category. A protected
mapping trigger requires a separate approval receipt before any such mapping
can be written.

The held-out C1 audit has 8 cases: 5 expected mapped categories and 3 expected
abstentions. Coverage is 0.6250, unresolved rate 0.3750, mapping precision
1.0000, exact-category agreement 1.0000, adjacent-category agreement 1.0000,
gross-category error 0.0000, and mean absolute ordinal category error 0.0000
on mapped known cases. Ordinal error distinguishes adjacent from gross errors
without treating category steps as equal physical distances.

These are roast-label normalization metrics, not flavor accuracy.
`C1_NORMALIZATION_DATA_SUFFICIENT=false` because the audit cases are
project-authored rather than an independent user sample.
