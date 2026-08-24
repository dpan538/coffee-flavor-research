# Black-coffee method comparisons

## Comparison matrix

| Context                | Principal process representation                             | Key metadata                                | V1 recommendation                              | Evidence status                       |
| ---------------------- | ------------------------------------------------------------ | ------------------------------------------- | ---------------------------------------------- | ------------------------------------- |
| Manual filter          | Percolation through filter                                   | geometry, material, recipe, TDS, extraction | broad family first; exact brewer optional      | DIRECTLY_SUPPORTED + DESIGN_INFERENCE |
| Batch filter           | Machine percolation                                          | basket, batch size, temperature, recipe     | distinct from manual leaf                      | DIRECTLY_SUPPORTED                    |
| French press           | Full immersion then screen separation                        | contact time, agitation, grind, decant      | immersion leaf                                 | DIRECTLY_SUPPORTED                    |
| AeroPress              | Variable immersion, pressure-assisted separation, filtration | recipe and orientation                      | polyhierarchical leaf                          | DESIGN_INFERENCE                      |
| Siphon                 | Immersion plus vacuum-assisted filtration                    | heat and timing                             | hybrid leaf                                    | DIRECTLY_SUPPORTED at process level   |
| Espresso               | Concentrated pressure extraction                             | dose/yield/time/temperature/pressure/TDS    | pressure family                                | DIRECTLY_SUPPORTED                    |
| Ristretto / lungo      | Espresso-family served styles                                | beverage ratio and extraction               | separate reported leaves, no universal cutoffs | UNRESOLVED boundaries                 |
| Americano / long black | Espresso plus added water                                    | espresso base, dilution, sequence           | distinct related leaves                        | UNRESOLVED terminology                |
| Moka                   | Heated, pressure-driven stovetop percolation                 | device and recipe                           | not espresso-equivalent                        | DIRECTLY_SUPPORTED at method level    |
| Cezve/Turkish-style    | Unfiltered boiled/decoction preparation                      | grind, boil cycles, settling                | separate leaf                                  | DIRECTLY_SUPPORTED at method level    |
| Cold-brew immersion    | Extended cool/ambient immersion                              | time, temperature, concentrate/dilution     | cold leaf                                      | DIRECTLY_SUPPORTED                    |
| Cold drip              | Cool percolation                                             | drip rate, time, concentration              | separate cold leaf                             | DIRECTLY_SUPPORTED at process level   |
| Nitro cold brew        | Cold-brew base plus nitrogen service                         | base brew, gas, dispense                    | beverage-style child                           | LIMITED DIRECT EVIDENCE               |

## Manual-filter resolution

Frost et al. found that basket geometry can change sensory quality and acceptance under controlled conditions ([doi:10.1111/1750-3841.14696](https://doi.org/10.1111/1750-3841.14696)). That is a reason to retain geometry when known, not a reason to ask every ordinary drinker whether the brewer was V60, Kalita Wave, Chemex, or Melitta.

V1 should ask the broad filter context. An optional second-level value may preserve `manual filter`, `batch filter`, and a specifically reported Chemex-style preparation. V60, Kalita Wave, and Melitta-style identities can be added later as source-specific or protocol metadata if evaluation shows a material ranking benefit.

## Americano versus long black

Published coffee sensory work does not provide a robust direct comparison that justifies equivalence or a stable sequence effect. Commercial and vocational descriptions show regional inconsistency in the names. Therefore:

- do not make them exact lexical variants;
- preserve each reported identity;
- relate both under diluted espresso;
- store espresso-to-water ratio and sequence when a study provides them;
- do not assign a sensory effect from the label alone.

This conclusion is `UNRESOLVED` at the universal terminology layer and a `DESIGN_INFERENCE` for the V0 schema.

## Long black versus cold brew

Long black starts with espresso-family pressure extraction and adds water. Cold brew uses extended low-temperature or ambient extraction. Studies of cold versus hot/full-immersion conditions show method, time, temperature, and roast effects that cannot be represented by a common leaf ([doi:10.1016/j.lwt.2021.111363](https://doi.org/10.1016/j.lwt.2021.111363); [doi:10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6)).

They may both be served black, but serving without milk is not sufficient computational identity. Recommendation: always distinct preparation contexts.

## AeroPress

The brewer can support short or long immersion, paper or metal filtration, inverted or standard orientation, varied agitation, and post-brew dilution. Labeling every use as only immersion or only percolation would create false precision.

Recommendation: one stable AeroPress identity with two active parents—immersion and hybrid/manual pressure—and protocol metadata for research. Do not create a universal AeroPress sensory profile.

## Concentration and dilution

Strength and extraction yield are major variables within coffee preparation. The controlled work behind the Brewing Control Chart and drip-brew experiments shows why served volume cannot stand in for extraction ([doi:10.1111/1750-3841.16531](https://doi.org/10.1111/1750-3841.16531); [doi:10.1038/s41598-020-73341-4](https://doi.org/10.1038/s41598-020-73341-4)).

The schema consequently distinguishes extraction method from post-extraction beverage style. Future studies can attach TDS, extraction yield, and dilution without changing concept identity.

## References

- Gloess AN et al. [doi:10.1007/s00217-013-1917-x](https://doi.org/10.1007/s00217-013-1917-x)
- Frost SC et al. [doi:10.1111/1750-3841.14696](https://doi.org/10.1111/1750-3841.14696)
- Batali ME et al. [doi:10.1038/s41598-020-73341-4](https://doi.org/10.1038/s41598-020-73341-4)
- Cotter AR et al. [doi:10.1111/1750-3841.16531](https://doi.org/10.1111/1750-3841.16531)
- Córdoba N et al. [doi:10.1016/j.lwt.2021.111363](https://doi.org/10.1016/j.lwt.2021.111363)
- Liang J et al. [doi:10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6)
