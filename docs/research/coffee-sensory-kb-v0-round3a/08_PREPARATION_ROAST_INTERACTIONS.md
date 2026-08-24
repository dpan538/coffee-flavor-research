# Preparation × roast interactions

## Conclusion

Preparation and roast must be retained jointly for future modeling. They should not be assumed independent, and Round 3A assigns no interaction coefficients.

## Direct evidence

Liang et al. used two roast treatments, three brewing temperatures, and five extraction times in full immersion. Roast was a major driver, while brewing temperature and time also structured sensory outcomes ([doi:10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6)). The design itself demonstrates why a dataset should preserve combinations rather than only marginal labels.

Frost et al. studied roast together with brew strength and extraction yield in drip coffee ([doi:10.1111/1750-3841.15326](https://doi.org/10.1111/1750-3841.15326)). The results make a one-variable roast rule scientifically inadequate.

Cordova et al. crossed medium/dark roast with black coffee, cow milk, and oat milk. Milk altered perception, and the pattern was not identical across roast and milk conditions ([doi:10.1021/acs.jafc.4c12852](https://doi.org/10.1021/acs.jafc.4c12852)). This supports retaining roast × milk context in later experiments.

## Examples

| Combination            | Why interaction may matter                               | Round 3A action                     |
| ---------------------- | -------------------------------------------------------- | ----------------------------------- |
| light roast × espresso | roast development, high concentration, extraction recipe | retain both; no flavor rule         |
| dark roast × filter    | roast treatment plus strength/extraction                 | retain both; no flavor rule         |
| light roast × milk     | coffee signal plus milk-derived and masking effects      | retain roast, milk type, proportion |
| dark roast × cold brew | roast plus temperature/time/contact regime               | retain all declared context         |

## Statistical implication

Future evaluation should compare at least:

1. sensory answers only;
2. sensory answers + preparation main effects;
3. sensory answers + roast main effects;
4. sensory answers + both contexts;
5. both contexts + prespecified interactions supported by sample size.

The held-out comparison should determine whether added terms improve retrieval/ranking calibration and abstention. Interaction parameters must be dataset-specific, regularized when appropriate, and accompanied by uncertainty.

## Data requirements

A suitable dataset should contain repeated observations across more than one preparation and roast condition, explicit protocols, independent sensory outcomes, and enough replication to distinguish interaction from confounding. The current Firstbloom corpus has no structured preparation or roast fields and cannot estimate these effects.

## Prohibited inference

These examples are invalid in Round 3A:

```text
dark roast → chocolate +0.35
cold brew → acidity -0.40
milk → sweetness +0.20
```

They lack declared population, measurement scale, model, uncertainty, and held-out validation. The database contains no such columns or seed values.

## Status

`PREPARATION_ROAST_INTERACTION_RESEARCH_PASS=true`, with the conclusion that interaction retention is justified and coefficient estimation is deferred.
