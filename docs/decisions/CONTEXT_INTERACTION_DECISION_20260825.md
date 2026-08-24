# Context interaction decision — 2026-08-25

Status: accepted, forward-only

Supersedes the current-interaction recommendations in Round 3A without
rewriting its migrations, audit receipt, research record, or five-level scheme.

## Decision

C0 is mandatory before sensory questions begin. The interaction offers exactly
the valid preparation families selected by the current C0 projection and no
`unknown`, `unsure`, or “I don't know” option.

C1 is mandatory and uses at least seven ordered project categories:

1. extremely light
2. light
3. medium-light
4. medium
5. medium-dark
6. dark
7. extremely dark

Medium-light and medium-dark are independent identities. The scale is ordinal;
its positions do not assert equal physical or sensory distance.

## Why five levels were superseded

The historical five-level scheme was an intentionally conservative Round 3A
recommendation. It collapses medium-light and medium-dark, distinctions used in
the target Mainland Chinese coffee context and required by the current product.
The new minimum is a product interaction contract, not a finding that seven
levels form a universal industry standard.

The database therefore retains `roast.scheme.project_v0_five_level` as a
historical, queryable scheme and introduces
`roast.scheme.project_v1_seven_level` as the current interaction scheme.

## Why C0 unknown was removed

Preparation constrains the sensory-reference problem. Ordinary users need only
identify a broad beverage context, not an academically exact mechanism: latte
can resolve to espresso plus milk, V60 to filter/percolation, French press to
immersion, and long black to espresso plus water. Unfamiliar or ambiguous
consumer wording is a resolver and curation problem, not a reason to add an
unknown interaction choice.

## Why database unknown states remain

Imported evidence can genuinely omit or obscure preparation and roast
metadata. `UNKNOWN`, `NOT_REPORTED`, `REPORTED_UNRESOLVED`, and
`NOT_APPLICABLE` therefore remain valid observation states. Production-safe
user projections exclude those statuses because observation uncertainty and a
user-selectable category are different concepts.

## Scientific boundary

Interaction constraints are product decisions. Scientific calibration remains
empirical. External labels, trade names, brew-intent labels, and measured color
systems map into the seven project categories only with reviewed evidence;
otherwise they remain unresolved.
