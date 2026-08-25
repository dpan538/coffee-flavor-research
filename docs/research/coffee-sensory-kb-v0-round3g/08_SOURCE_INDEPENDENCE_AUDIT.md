# Source independence audit

Two canonical origins count as independent:

- `origin.doi.10.17632.m3n2gc4dv6.1` — the Universitas Jember coffee-sensory
  study; its paper, Mendeley record, workbook and aggregate TSV are one family.
- `origin.wikimedia.wiktionary.revision-set-20260825` — the English and Chinese
  exact-revision metadata sources, conservatively grouped as one family.

The second origin is independent from the coffee study, but its two language
editions are not counted twice and do not constitute independent bilingual
review. No Mendeley hosting relationship makes unrelated studies independent
or dependent by itself; origin is the research project, not the repository.

A partial unique index prevents two independently countable families from
sharing one canonical origin. Mirrors must have
`counts_as_independent=false`. Cross-source promotion counts distinct
canonical origins attached to threshold-qualified supporting claims. No
cross-source promotion occurs in Round 3G.
