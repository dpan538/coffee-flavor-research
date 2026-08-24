# Product context recommendation

## C0 recommendation

Ask one broad preparation question with eight method families. Offer a second-level choice only when it materially preserves a known beverage identity.

```text
filter / percolation
immersion
hybrid / manual pressure
espresso / short pressure
espresso + water
stovetop / boiled
cold extraction
espresso + milk
I don't know
```

The “I don’t know” response is a status outside the eight choices.

### Conditional second level

- Espresso / short pressure: espresso, ristretto, lungo.
- Espresso + water: Americano, long black, or broader family when unknown.
- Cold extraction: immersion cold brew, cold drip, nitro, or broader family.
- Espresso + milk: flat white, latte, cappuccino, cortado, piccolo, macchiato, or broader family.
- Stovetop / boiled: moka, cezve/Turkish-style, or broader family.
- Filter: manual versus batch is useful; exact enthusiast brewer is optional.
- Immersion/hybrid: preserve French press, AeroPress, siphon when the user knows them.

`RECOMMENDED_C0_SECOND_LEVEL_REQUIRED=conditional`.

## C1 recommendation

Use five coarse ordered choices plus unknown:

```text
very light
light
medium
dark
very dark
I don't know
```

The five labels are interaction bins, not a roast standard. Do not show measurements or imply equal spacing. When packaging reports medium-light, medium-dark, Nordic, City, filter roast, espresso roast, or omniroast, preserve the phrase and normalize only through a reviewed source-aware rule.

`SEVEN_LEVEL_ROAST_HYPOTHESIS=rejected_for_v1_use_five_coarse_levels`.

## Milk mode

Milk beverages remain in C0 because the target product includes ordinary café drinking. Future ranking should condition through a milk-coffee mode, with milk identity/proportion captured when feasible. If data remain insufficient, evaluation may temporarily abstain or restrict coverage, but the product contract should not silently treat a latte as black espresso.

## Additives

Strongly flavored beverages are outside the default V1 coffee-reference evaluation population. Store explicit additions as context and route them to a future composite-beverage mode. Ingredient-derived vanilla, chocolate, spice, or fruit is not evidence about the coffee bean.

## Future typed interface

Conceptual only—no API or ranking implementation is added in Round 3A:

```text
CandidateRankingInput {
  preparation_context: {
    status: KNOWN | REPORTED_UNRESOLVED | UNKNOWN | NOT_REPORTED
    family?: PreparationFamilyKey
    subtype?: PreparationConceptKey
    reported_expression?: string
    additions?: BeverageAdditionContext[]
  }
  roast_context: {
    status: KNOWN | REPORTED_UNRESOLVED | UNKNOWN | NOT_REPORTED
    normalized_category?: ProjectRoastCategoryKey
    reported_expression?: string
    source_scheme?: RoastSchemeKey
    measurement?: RoastMeasurement
  }
  sensory_answers: SensoryAnswer[]
}
```

Preparation and roast are typed conditions. They are not appended to sensory answers as descriptor scores.

## Evaluation before product use

Before C0/C1 affects candidate ranking:

1. validate ordinary-user comprehension of the eight-family and five-level interaction;
2. acquire rights-cleared multi-preparation/multi-roast data;
3. define development and held-out splits before coefficient tuning;
4. compare context-free, main-effect, and interaction models;
5. measure ranking metrics, calibration where meaningful, coverage, and abstention error;
6. report black and milk modes separately;
7. retain an explicit unknown-context baseline.

## Product-language constraint

Use “context-compatible candidates,” “closest references,” and “also consider.” Do not call the result true flavor, correct answer, or flavor accuracy.
