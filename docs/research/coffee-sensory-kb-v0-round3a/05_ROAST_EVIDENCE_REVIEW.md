# Roast evidence review

## Research question

How should an ordinary user’s roast context be retained without converting subjective labels into a universal physical scale or flavor score?

## Roast is consequential but not a single standardized label

Controlled studies support roast as an important experimental factor. Frost, Ristenpart, and Guinard found that roast, brew strength, and extraction yield affected drip-coffee sensory quality ([doi:10.1111/1750-3841.15326](https://doi.org/10.1111/1750-3841.15326)). Liang et al. reported roast as a major source of separation in a full-immersion experiment that also varied temperature and time ([doi:10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6)).

These results do not establish universal boundaries for “light,” “medium,” or “dark.” In each experiment, roast treatment is defined by that protocol and material. A label from one roaster or study cannot be assumed to match another.

## Measured roast color

Yeager et al. used Agtron Gourmet and CIELAB measurements to study roast level and brewed-coffee color ([doi:10.1111/1750-3841.16089](https://doi.org/10.1111/1750-3841.16089)). SCA’s public standards page now lists an SCA-131 Coffee Roast Level test method, while SCA’s roast-color research materials describe continuing work on measurement and designation ([SCA standards](https://sca.coffee/research/coffee-standards/); [SCA roast-color overview](https://sca.coffee/sca-news/coffee-decoded-4-roast-color)).

Round 3A records measurement method, material basis, value, and direction. Whole-bean and ground measurements remain distinct. No measured value is automatically converted to a five-level user label because a validated cross-instrument mapping has not been adopted.

## Epistemic objects

| Object                      | Example                      | Meaning                                         |
| --------------------------- | ---------------------------- | ----------------------------------------------- |
| User-selected roast         | “I think it is dark”         | Interaction response                            |
| Roaster-declared label      | “medium-light”               | Source assertion within that roaster’s language |
| Project-normalized category | `roast.project.medium`       | Coarse project interaction bin                  |
| Measured value              | Agtron or CIELAB reading     | Method-specific empirical measurement           |
| Measurement method          | Agtron Gourmet, ground basis | Instrument/protocol identity                    |
| Roast style label           | “espresso roast”             | Intended use or style; not necessarily darkness |
| Source-scheme category      | “City” in a declared scheme  | Recoverable source-local category               |

Conflating any two of these loses provenance.

## Terminology findings

### Light / medium / dark

Useful common ordinal language. Boundaries remain source-specific. A three-level source scheme is represented and maps only approximately to the project scale.

### City, City+, Full City, Vienna, French, Italian

Traditional trade terms may imply ordering within particular practices, but universal measurement cutoffs and regional use are not stable enough for project normalization. They remain source/industry terminology. `City+` is documented as an open lexical item rather than silently merged with City or Full City.

### Filter roast, espresso roast, omniroast

These principally communicate intended brewing use or roaster strategy. They are not normalized darkness categories.

### Nordic roast

A regional/style expression with variable use. It is not forced to `light`.

### Extremely light and extremely dark

Understandable relative phrases, but the original seven-label proposal combines extremes and intermediate labels without validated boundaries. They remain unresolved source/user expressions rather than extra V0 bins.

## Three, five, or seven user choices

| Scale    | Advantage                                            | Risk                                                                           | Decision                                      |
| -------- | ---------------------------------------------------- | ------------------------------------------------------------------------------ | --------------------------------------------- |
| 3 levels | lowest burden; aligns with common labels             | loses meaningful extremes; many packages use intermediate language             | retained as source scheme, not project target |
| 5 levels | moderate burden; represents broad extremes           | still subjective; boundaries not standardized                                  | recommended interaction projection            |
| 7 levels | preserves medium-light and medium-dark plus extremes | higher cognitive and normalization burden; apparent precision exceeds evidence | rejected for V1                               |

The five labels are “very light / light / medium / dark / very dark.” They are ordered but not interval-scaled. The database stores ordinal positions for sorting only.

## Unknown

`unknown` is a valid observation status. It is neither a sixth roast category nor an alias for medium. A future model may marginalize over missing context using explicit logic and evaluated data; Round 3A performs no imputation.

## Evidence limitations

- SCA’s standard content and member materials are not reproduced. Only public metadata and independently authored interpretation are stored.
- Instrument scales require declared method, preparation basis, and calibration. Cross-instrument equivalence is outside this round.
- Roast development profile, end temperature, color, mass loss, and time are related but non-interchangeable variables.
- Consumer ability to select five levels has not yet been validated in the target interaction.

## References

- Frost SC, Ristenpart WD, Guinard JX. _Journal of Food Science_ (2020). [doi:10.1111/1750-3841.15326](https://doi.org/10.1111/1750-3841.15326)
- Yeager SE et al. _Journal of Food Science_ (2022). [doi:10.1111/1750-3841.16089](https://doi.org/10.1111/1750-3841.16089)
- Liang J et al. _Scientific Reports_ (2024). [doi:10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6)
- Cordova N et al. _Journal of Agricultural and Food Chemistry_ (2025). [doi:10.1021/acs.jafc.4c12852](https://doi.org/10.1021/acs.jafc.4c12852)
- SCA. [Coffee standards](https://sca.coffee/research/coffee-standards/) and [roast-color research overview](https://sca.coffee/sca-news/coffee-decoded-4-roast-color), retrieved 2026-08-25.
