# Preparation taxonomy

## Scope and semantics

This is the project V0 organizational projection for C0. A parent means “broader preparation context,” not “same sensory profile,” “perceptually close,” or “interchangeable recipe.” Multiple parents are permitted.

Stable keys, not UI labels, define identity. `unknown` is modeled as observation status and is deliberately absent from the taxonomy.

## Recommended top-level C0 choices

| Order | Stable key                              | Consumer-visible family   | Conditional subtype? |
| ----: | --------------------------------------- | ------------------------- | -------------------- |
|     1 | `preparation.family.filter_percolation` | Filter / percolation      | optional             |
|     2 | `preparation.family.immersion`          | Immersion                 | optional             |
|     3 | `preparation.family.hybrid`             | Hybrid / manual pressure  | optional             |
|     4 | `preparation.family.espresso_pressure`  | Espresso / short pressure | yes                  |
|     5 | `preparation.family.diluted_espresso`   | Espresso + water          | yes                  |
|     6 | `preparation.family.stovetop_boiled`    | Stovetop / boiled         | useful               |
|     7 | `preparation.family.cold_extraction`    | Cold extraction           | yes                  |
|     8 | `preparation.family.espresso_milk`      | Espresso + milk           | yes                  |

An “I don’t know” response is additionally valid but is not counted as a method choice.

## Hierarchy

```text
filter / percolation
├── manual filter
│   ├── pour-over cone
│   └── Chemex-style filter
└── batch filter

immersion
├── French press
├── other immersion
└── AeroPress  ─────────────┐
                            │ multi-parent
hybrid / manual pressure    │
├── AeroPress  ◀────────────┘
└── siphon / vacuum

espresso / short pressure
├── espresso
├── ristretto
└── lungo

espresso + water
├── Americano
└── long black

stovetop / boiled
├── moka
└── cezve / Turkish-style

cold extraction
├── cold-brew immersion
│   └── nitro cold brew
└── cold drip

espresso + milk
├── flat white
├── latte
├── cappuccino
├── cortado
├── piccolo
└── macchiato
```

There are 8 active families and 22 active leaves. Intermediate `manual filter` and `cold-brew immersion` nodes allow a broader source report to remain useful without pretending to know its leaf.

## Mandatory distinctions

### Flat white and latte

They share `preparation.family.espresso_milk` and remain separate leaves. The shared parent permits one broad conditional mode; separate leaves preserve explicitly reported recipe identity. No universal ratio or foam cutoff is encoded.

### Americano and long black

They are distinct leaves under `preparation.family.diluted_espresso` with a symmetric `related_to` assertion. They are not lexical synonyms. This is a conservative project interpretation because direct sensory comparison evidence is weak and regional naming varies.

### Long black and cold brew

They share no computational preparation leaf. Their only potential common ancestor is an informal “black/no-milk beverage” presentation, which is intentionally not used as a normalization target. Espresso extraction plus dilution and extended cool extraction remain separate.

### AeroPress

AeroPress is a multi-parent method under both immersion and hybrid/manual-pressure organization. Recipe details must remain available for research. The taxonomy does not claim that every AeroPress recipe uses both mechanisms to the same degree.

### Nitro cold brew

Nitro is a beverage-style child of cold-brew immersion because nitrogenation is a service operation, not a new bean extraction family.

## Lexical policy

One independently authored preferred English expression is seeded for each context identity. `drip coffee` and `iced coffee` remain unresolved:

- `drip coffee` can refer to batch filter, manual filter, or—in some usages—cold drip.
- `iced coffee` can be hot-brewed coffee served over ice or a cold-extracted beverage.

The database does not choose the nearest target merely to increase coverage.

## Scientific metadata not required from the user

Future observation metadata may include brewer geometry, filter material, dose, beverage mass, water temperature, contact time, TDS, extraction yield, espresso pressure/profile, added-water amount, milk identity/proportion, and serving temperature. Their availability does not imply they should all become questions.

## Governance

All taxonomy edges point to a versioned project source and assertion role. Empirical sources support selected context boundaries, while the organizational hierarchy is explicitly project-authored. No preparation context is inserted into `kb.concept`.
