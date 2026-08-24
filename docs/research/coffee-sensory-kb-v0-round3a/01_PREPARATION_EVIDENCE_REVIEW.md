# Preparation evidence review

## Research question

Which preparation information is useful before a low-burden sensory interaction, and which information belongs only in a scientific protocol?

## Evidence summary

Preparation name is an imperfect proxy for a bundle of variables. Coffee-specific studies support retaining preparation context, but they also show why the name cannot be converted directly into a flavor vector.

Gloess et al. compared nine common preparations using process, instrumental, and sensory measurements. The study supports distinct method identities, including pressure and longer-beverage methods, without establishing one universal profile for each name ([doi:10.1007/s00217-013-1917-x](https://doi.org/10.1007/s00217-013-1917-x)). Sanchez and Chambers likewise demonstrated that preparation changes product sensory properties in coffee ([doi:10.1111/joss.12184](https://doi.org/10.1111/joss.12184)).

Within a method family, controlled variables can dominate. Batali et al. found little sensory effect from brew-temperature changes within 87–93 °C when total dissolved solids and percent extraction were held constant ([doi:10.1038/s41598-020-73341-4](https://doi.org/10.1038/s41598-020-73341-4)). The new Brewing Control Chart work treats brew ratio, strength, and extraction as related protocol variables rather than simple method labels ([doi:10.1111/1750-3841.16531](https://doi.org/10.1111/1750-3841.16531)).

Filter geometry can still produce detectable effects. Frost et al. found sensory and acceptance differences for basket geometry under controlled drip-brew conditions ([doi:10.1111/1750-3841.14696](https://doi.org/10.1111/1750-3841.14696)). This supports optional brewer/geometry metadata, but not a mandatory V1 choice among every enthusiast dripper.

Cold extraction should remain distinct. Córdoba et al. compared cold and hot brewing with sensory and physicochemical outcomes ([doi:10.1016/j.lwt.2021.111363](https://doi.org/10.1016/j.lwt.2021.111363)). Liang et al. studied full immersion across roast, temperature, and time and found that these variables jointly structured results ([doi:10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6)).

## Consumer-visible category versus scientific metadata

| Variable                              |            V1 consumer context | Scientific/protocol metadata | Evidence status                                                         |
| ------------------------------------- | -----------------------------: | ---------------------------: | ----------------------------------------------------------------------- |
| Broad extraction family               |                            yes |                          yes | DIRECTLY_SUPPORTED                                                      |
| Exact brewer/model                    |                     usually no |                     optional | DESIGN_INFERENCE informed by filter-geometry evidence                   |
| Percolation/immersion/pressure phases |        represented by taxonomy |                          yes | DIRECTLY_SUPPORTED at method level                                      |
| Water temperature                     |             no extra C0 burden |                          yes | DIRECTLY_SUPPORTED but conditional on other variables                   |
| Contact time                          |             no extra C0 burden |                          yes | DIRECTLY_SUPPORTED                                                      |
| Filtration material/geometry          |                  no by default |                     optional | DIRECTLY_SUPPORTED in controlled contexts                               |
| TDS / beverage strength               |             no unless measured |                          yes | DIRECTLY_SUPPORTED                                                      |
| Percent extraction                    |             no unless measured |                          yes | DIRECTLY_SUPPORTED                                                      |
| Post-extraction water                 |               beverage subtype |                          yes | DESIGN_INFERENCE with clear process semantics                           |
| Milk presence/type/proportion         | family plus ingredient context |                          yes | DIRECTLY_SUPPORTED                                                      |
| Foam/texture                          |               subtype metadata |                          yes | SUPPORTED BY TRANSFERABLE METHOD; named-drink standardization is weak   |
| Nitrogen service                      |          cold-beverage subtype |                          yes | DIRECTLY SUPPORTED as a product form; sensory generalization is limited |

## Preparation groups considered

- Manual and batch filter/percolation
- Immersion, including French press
- Hybrid methods, including AeroPress and siphon/vacuum
- Espresso-family pressure extraction: espresso, ristretto, lungo
- Diluted espresso: Americano and long black
- Stovetop pressure-percolation and boiled coffee: moka and cezve/Turkish-style
- Cold extraction: immersion cold brew and cold drip
- Post-extraction nitrogenation: nitro cold brew
- Espresso-and-milk beverage styles

## Limitations and disagreements

- “Method” is not a randomized sensory treatment across all published studies; bean, roast, water, grinder, recipe, strength, and serving temperature often co-vary.
- Direct peer-reviewed sensory comparisons of Americano and long black were not found. Commercial descriptions establish terminology only.
- AeroPress recipes vary widely in immersion time, filtration, pressure, dilution, and orientation. A single method label under-specifies the experiment.
- Named milk drinks are regionally variable. The project can preserve consumer-visible identities while avoiding universal ratio definitions.
- Nitro cold brew literature is smaller than hot/filter and ordinary cold-brew literature. Nitrogenation is best recorded as a serving operation.

## Conclusion

Use a small consumer-facing hierarchy, store exact protocol variables when explicitly known, and abstain when the source reports only an ambiguous label. Preparation context should later condition a calibrated model, not provide deterministic flavor points.

## References

- Gloess AN et al. _European Food Research and Technology_ (2013). [doi:10.1007/s00217-013-1917-x](https://doi.org/10.1007/s00217-013-1917-x)
- Sanchez K, Chambers E. _Journal of Sensory Studies_ (2015). [doi:10.1111/joss.12184](https://doi.org/10.1111/joss.12184)
- Batali ME et al. _Scientific Reports_ (2020). [doi:10.1038/s41598-020-73341-4](https://doi.org/10.1038/s41598-020-73341-4)
- Frost SC et al. _Journal of Food Science_ (2019). [doi:10.1111/1750-3841.14696](https://doi.org/10.1111/1750-3841.14696)
- Cotter AR et al. _Journal of Food Science_ (2023). [doi:10.1111/1750-3841.16531](https://doi.org/10.1111/1750-3841.16531)
- Córdoba N et al. _LWT_ (2021). [doi:10.1016/j.lwt.2021.111363](https://doi.org/10.1016/j.lwt.2021.111363)
- Liang J et al. _Scientific Reports_ (2024). [doi:10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6)
