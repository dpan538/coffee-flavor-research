# Open questions

## Highest priority

1. Can ordinary home/café users reliably choose among eight broad C0 families without extra explanation?
2. Does an optional subtype improve future ranking enough to justify burden, and for which families?
3. Can users distinguish five roast labels consistently across packaging, visual bean appearance, and café information?
4. What source-aware mappings are defensible for medium-light and medium-dark?
5. What rights-cleared dataset can cross multiple preparation families and multiple roast levels with sensory outcomes?
6. How should black-coffee and milk-coffee held-out evaluation be stratified?

## Preparation

- Direct sensory evidence comparing Americano and long black under controlled ratios and serving conditions is missing.
- AeroPress protocol variables need a versioned data model before empirical effects can be estimated.
- The product value of distinguishing V60, Kalita Wave, Chemex, Melitta-style, and other drippers is unvalidated.
- Siphon, phin, pod/capsule, instant, cowboy/boiled, South Indian filter, and additional regional methods may need source-specific extension. Their omission is not a claim of irrelevance.
- Nitro service evidence is smaller than the evidence for ordinary cold extraction.
- “Iced coffee” requires a disambiguation strategy that does not equate temperature at serving with extraction temperature.

## Milk and additions

- Named drink ratios and foam definitions vary regionally; no universal flat-white/latte boundary is encoded.
- Plant-milk formulation, fat/protein content, sweetening, and barista additives may matter more than the plant source name alone.
- The minimum data needed to distinguish milk masking from the coffee signal is unresolved.
- Criteria for admitting a composite-beverage mode are not defined.

## Roast

- SCA roast-color standardization is evolving; Round 3A does not reproduce or preempt it.
- Cross-device mappings among Agtron, CIELAB, and other color systems need versioned calibration data.
- Whole-bean versus ground measurement differences need an explicit protocol in any imported dataset.
- City+, Half City, Cinnamon, New England, continental, Spanish, and other labels require source-specific rights and semantic review.
- “Nordic roast” may combine region, style, development, intended use, and marketing; no single normalized target is justified.
- Five-level user comprehensibility remains a product hypothesis, even though it is preferable to the unsupported seven-level scale.

## Modeling and evaluation

- Whether preparation and roast improve ranking beyond sensory answers must be measured, not assumed.
- Interactions require enough crossed observations and must not be learned from roaster-language frequency alone.
- Unknown-context behavior needs an explicit benchmark.
- The future model must distinguish missing at random, source-not-reported, user-does-not-know, and reported-but-unresolved contexts.
- No embedding or ranking benchmark should begin until imported context data have frozen versions and leakage-safe splits.

## Governance

- The three Dryad candidates require exact version/file/hash receipts before raw import.
- Article licences and dataset licences remain separate.
- Source-specific terminology can be extended without changing the project target scheme.
- Every new context mapping must keep its source/version, role, locator, rights, and uncertainty.

## Explicitly unresolved labels

Preparation: `drip coffee`, `iced coffee`.

Roast: `extremely light`, `medium-light`, `medium-dark`, `extremely dark`, `City roast`, `Full City roast`, `Vienna roast`, `French roast`, `Italian roast`, `Nordic roast`, `filter roast`, `espresso roast`, `omniroast`.

These queues are deliberate abstentions, not missing cleanup.
