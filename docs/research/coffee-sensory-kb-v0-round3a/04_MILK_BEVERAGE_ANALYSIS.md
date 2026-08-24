# Milk beverage analysis

## Decision

Adopt a future conditional milk-coffee mode (Model B): black-coffee and milk-coffee ranking should share the canonical sensory knowledge base but must not assume one calibrated observation model. Round 3A implements representation only; it does not train either model.

## Evidence

Milk can change both the beverage matrix and the perception task. Itobe, Nishimura, and Kumazawa compared black coffee with milk coffee and associated reduced coffee-like aroma intensity with changes in the release of selected odorants ([doi:10.3136/fstr.21.607](https://doi.org/10.3136/fstr.21.607)). Earlier work also reported effects of milk addition on espresso aroma and sensory properties ([doi:10.3136/fstr.15.233](https://doi.org/10.3136/fstr.15.233)).

Cordova et al. evaluated medium- and dark-roast Arabica with 30% cow or oat milk. Milk introduced its own dairy-like or caramel/vanilla-like impressions and reduced coffee-related flavor perception; effects varied by roast and milk type ([doi:10.1021/acs.jafc.4c12852](https://doi.org/10.1021/acs.jafc.4c12852)). This directly rejects the assumption that `milk_context` is always a harmless binary covariate.

The evidence is sufficient to preserve milk identity, proportion, and beverage style as context. It is not sufficient to assign general coefficients for bitterness, acidity, sweetness, or aroma across all recipes and alternative-milk products.

## Model comparison

| Model                                               | Assessment                                                                                                                                                                          |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A — one universal model with a milk flag            | Not recommended as the default hypothesis. It risks pooling different perceptual regimes and ingredient-derived notes. It may be benchmarked later as an ablation.                  |
| B — conditional black-coffee and milk-coffee models | Recommended. Both can use the same ontology and output contract while calibration and uncertainty remain context-specific.                                                          |
| C — black coffee only                               | Too restrictive for the stated home/café product, but acceptable as an initial evaluation subset if milk data are insufficient. It must not be presented as final product coverage. |

## Flat white versus latte

Flat white and latte can share one broad computational parent: `espresso + milk`. They should remain different leaf subtypes.

Rationale:

- both use an espresso-family base and milk, so they share the major context shift identified by milk research;
- milk quantity, beverage volume, and foam/texture can alter coffee signal strength and mouthfeel;
- café definitions and ratios vary by region, shop, cup, and recipe;
- merging the names would discard explicit source information, while hard-coding universal recipe thresholds would invent a standard.

The same approach extends to cappuccino, cortado, piccolo, and macchiato: shared parent, distinct reported leaves, optional recipe metadata. A future empirical study may find that some leaves can share one model stratum, but the database should not erase them in advance.

## Alternative milk

Cow and oat milk produced different patterns in the 2025 study. Oat, soy, almond, coconut, and other plant products also vary substantially by formulation. Round 3A therefore includes an extensible addition hierarchy but does not claim a complete alternative-milk ontology.

Minimum future observation fields are:

- milk present/absent/unknown/not reported;
- broad dairy versus plant-based type;
- exact product or subtype when explicit;
- approximate proportion or recipe when measured;
- heated/foamed state when explicit;
- beverage style label and serving volume when explicit.

## Added-flavor boundary

Sugar, syrup, chocolate, cream, spices, tonic, fruit juice, ice cream, alcohol, and other additions are beverage context. Ingredient flavor cannot evidence a bean sensory attribute.

V1 recommendation:

- permit explicit ingredient-context metadata;
- exclude strongly flavored drinks from the default coffee-reference ranking/evaluation population;
- retain them for a future composite-beverage mode;
- never promote an additive label to `kb.concept` through context ingestion;
- abstain if the ingredient contribution cannot be separated from coffee perception.

A vanilla syrup observation may be useful for serving-context analysis. It is not provenance for `sensory.vanilla` in the coffee.

## Uncertainty

Direct comparative literature for named café drinks is much weaker than the literature for milk addition itself. The leaf recommendation is therefore a governance-preserving design inference, not a claim that every flat white is sensorially distinguishable from every latte.

## References

- Itobe T, Nishimura O, Kumazawa K. _Food Science and Technology Research_ (2015). [doi:10.3136/fstr.21.607](https://doi.org/10.3136/fstr.21.607)
- Akiyama M et al. _Food Science and Technology Research_ (2009). [doi:10.3136/fstr.15.233](https://doi.org/10.3136/fstr.15.233)
- Bücking M, Steinhart H. _Journal of Agricultural and Food Chemistry_ (2002). [doi:10.1021/jf011117p](https://doi.org/10.1021/jf011117p)
- Cordova N et al. _Journal of Agricultural and Food Chemistry_ (2025). [doi:10.1021/acs.jafc.4c12852](https://doi.org/10.1021/acs.jafc.4c12852)
