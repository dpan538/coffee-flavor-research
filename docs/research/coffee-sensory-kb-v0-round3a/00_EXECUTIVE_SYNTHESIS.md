# Round 3A executive synthesis

## Decision

Round 3A establishes preparation and roast as governed contextual conditions. They are not sensory attributes, flavor probabilities, or deterministic ranking weights.

The V0 product recommendation is:

- C0 uses eight broad preparation choices: filter/percolation, immersion, hybrid/manual pressure, espresso/short pressure, espresso plus water, stovetop/boiled, cold extraction, and espresso plus milk.
- A second-level choice is conditional. It is useful for espresso styles, diluted espresso, cold extraction, and milk beverages; exact manual-filter brewer is optional metadata rather than a mandatory V1 question.
- C1 uses five coarse ordered labels: very light, light, medium, dark, and very dark. The labels have no universal physical cutoffs and are not assumed equally spaced.
- `unknown` is a response status for both C0 and C1. It is not a preparation leaf and is never imputed to medium roast.
- Source labels, measured roast values, project-normalized categories, and brew-intent labels are separate records.
- Future milk-coffee work should use a conditional milk mode, not assume that the black-coffee model transfers unchanged.

## Evidence status

| Conclusion                                                                          | Status                                                                               | Basis                                                                                     |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Preparation can change measured and perceived beverage properties                   | DIRECTLY_SUPPORTED                                                                   | Multi-method and controlled coffee studies                                                |
| Strength, extraction yield, recipe, and filtration can matter within a named method | DIRECTLY_SUPPORTED                                                                   | Controlled brew studies                                                                   |
| Long black and cold brew are not one computational leaf                             | DIRECTLY_SUPPORTED for extraction distinction; DESIGN_INFERENCE for product grouping | Pressure/dilution versus extended cool extraction                                         |
| Americano and long black are distinct related leaves                                | UNRESOLVED terminology plus DESIGN_INFERENCE                                         | Direct sensory comparison is absent; regional naming varies                               |
| Flat white and latte are distinct leaves under one milk parent                      | DIRECTLY_SUPPORTED for milk effects; DESIGN_INFERENCE for named leaves               | Milk amount and formulation alter perception; named recipes are not globally standardized |
| AeroPress is polyhierarchical                                                       | DESIGN_INFERENCE                                                                     | Recipe variability prevents a single universal extraction identity                        |
| Preparation and roast may interact                                                  | DIRECTLY_SUPPORTED                                                                   | Full-immersion roast/temperature/time and milk/roast experiments                          |
| Five user roast levels are scientifically calibrated categories                     | NOT SUPPORTED                                                                        | Five levels are a low-burden interaction projection, not a standard                       |
| The proposed seven levels should be used in V1                                      | REJECTED FOR V1                                                                      | Increased label burden without reliable cross-source boundaries                           |

## Scientific boundary

The evidence supports retaining context for later conditioning. It does not support rules such as “dark roast adds 0.35 chocolate” or “cold brew removes 0.4 acidity.” Future effects must be learned from a declared dataset and evaluated on held-out observations.

The new PostgreSQL `context` domain therefore records:

- stable preparation identities and polyhierarchy;
- context expressions and explicitly unresolved labels;
- source-specific roast schemes;
- a separate project user scale;
- cautious mappings with provenance and certainty roles;
- observation-level known, unresolved, unknown, not-reported, and not-applicable states;
- beverage additions and measured roast values;
- rights-reviewed candidate datasets.

It does not modify the 130-concept ontology, the 92 active sensory attributes, or the frozen Round 2B corpus snapshot.

## Key evidence

- Gloess et al. compared nine extraction methods and reported method-related instrumental and sensory differences: [doi:10.1007/s00217-013-1917-x](https://doi.org/10.1007/s00217-013-1917-x).
- Batali et al. found that, when brew strength and extraction were fixed, changing drip-brew temperature within the studied range had little sensory impact: [doi:10.1038/s41598-020-73341-4](https://doi.org/10.1038/s41598-020-73341-4).
- Frost et al. reported effects of brew strength, extraction yield, and roast in drip coffee: [doi:10.1111/1750-3841.15326](https://doi.org/10.1111/1750-3841.15326).
- Liang et al. retained roast, temperature, and contact time in a full-immersion factorial study: [doi:10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6).
- Cordova et al. found that cow and oat milk changed coffee perception and interacted with roast treatment: [doi:10.1021/acs.jafc.4c12852](https://doi.org/10.1021/acs.jafc.4c12852).
- SCA states that roast-color standardization remains an active research area and distinguishes quantitative color measurement from qualitative roast labels: [SCA roast-color overview](https://sca.coffee/sca-news/coffee-decoded-4-roast-color).

Detailed evidence, limitations, rights, and the schema contract are in the remaining Round 3A research documents.
