# Round 2B corpus statistics

Date: 2026-08-24

Corpus version: `firstbloom-a6cb002-pilot-v1`

## Interpretation rule

Every measurement in this document describes language use in the frozen
historical pilot. Frequency is not sensory validity, co-occurrence is not
perceptual similarity, and normalized pointwise mutual information (NPMI) is
not a canonical ontology relation.

The authoritative rows are the
[frequency inventory](../../../db/data/round2b/pilot_expression_statistics.tsv),
[co-occurrence inventory](../../../db/data/round2b/pilot_cooccurrence.tsv), and
[staged diagnostics](../../../db/data/round2b/pilot_diagnostics.json). Their
hashes and method configuration are bound by the
[generation receipt](../../../db/data/round2b/generation_receipt.json).

## Frequency and long tail

The pilot contains 5,564 retained phrase occurrences and 1,713 unique
normalized expressions across 2,474 documents and 215 publishers.

| Expression-frequency band | Normalized expressions |
| ------------------------- | ---------------------: |
| 1                         |                  1,268 |
| 2                         |                    185 |
| 3–5                       |                    111 |
| 6–10                      |                     59 |
| 11–25                     |                     50 |
| 26–50                     |                     18 |
| 51 or more                |                     22 |

Hapax expressions account for 1,268 of 1,713 normalized expressions
(`74.022183%`). The 25 highest-frequency expressions account for 1,761 of 5,564
occurrences (`31.649892%`), and the top 100 account for 3,185 occurrences
(`57.242991%`). The complete 1,713-row frequency inventory preserves the full
rankable result rather than truncating it to a display list.

### Top 25 normalized expressions

| Rank | Expression     | Occurrences | Documents | Publishers |
| ---: | -------------- | ----------: | --------: | ---------: |
|    1 | caramel        |         169 |       169 |         99 |
|    2 | dark chocolate |         114 |       114 |         74 |
|    3 | honey          |         103 |       103 |         69 |
|    4 | floral         |          91 |        89 |         57 |
|    5 | milk chocolate |          83 |        83 |         58 |
|    6 | cherry         |          81 |        81 |         63 |
|    7 | brown sugar    |          76 |        76 |         54 |
|    8 | chocolate      |          76 |        76 |         48 |
|    9 | peach          |          70 |        70 |         50 |
|   10 | raspberry      |          70 |        70 |         50 |
|   11 | apricot        |          67 |        67 |         54 |
|   12 | cocoa          |          67 |        67 |         49 |
|   13 | plum           |          64 |        64 |         54 |
|   14 | orange         |          61 |        60 |         44 |
|   15 | strawberry     |          58 |        58 |         45 |
|   16 | citrus         |          56 |        56 |         48 |
|   17 | blackberry     |          55 |        55 |         47 |
|   18 | jasmine        |          55 |        55 |         48 |
|   19 | sweet          |          55 |        55 |         37 |
|   20 | vanilla        |          53 |        53 |         45 |
|   21 | black tea      |          51 |        51 |         39 |
|   22 | lemon          |          51 |        51 |         39 |
|   23 | lime           |          47 |        47 |         33 |
|   24 | almond         |          44 |        44 |         35 |
|   25 | blackcurrant   |          44 |        44 |         36 |

### Ranks 26–100

The remainder of the top 100 is shown compactly as `expression (occurrences)`.

| Rank | Expression (occurrences) | Rank | Expression (occurrences) | Rank | Expression (occurrences) |
| ---: | ------------------------ | ---: | ------------------------ | ---: | ------------------------ |
|   26 | toffee (42)              |   51 | cacao (21)               |   76 | lychee (13)              |
|   27 | tangerine (40)           |   52 | nutty (21)               |   77 | panela (13)              |
|   28 | apple (38)               |   53 | black cherry (20)        |   78 | pecan (13)               |
|   29 | mango (38)               |   54 | green apple (20)         |   79 | clean (12)               |
|   30 | grapefruit (34)          |   55 | hibiscus (20)            |   80 | concord grape (12)       |
|   31 | hazelnut (34)            |   56 | blueberry (19)           |   81 | lavender (12)            |
|   32 | juicy (34)               |   57 | cola (19)                |   82 | rich (12)                |
|   33 | pineapple (34)           |   58 | dried fruit (19)         |   83 | tropical fruits (12)     |
|   34 | red apple (32)           |   59 | nuts (19)                |   84 | complex (11)             |
|   35 | raisin (30)              |   60 | syrupy (19)              |   85 | fruity (11)              |
|   36 | creamy (29)              |   61 | blood orange (18)        |   86 | green grape (11)         |
|   37 | molasses (29)            |   62 | maple syrup (18)         |   87 | honeydew (11)            |
|   38 | nectarine (27)           |   63 | nougat (18)              |   88 | honeysuckle (11)         |
|   39 | bergamot (26)            |   64 | red grape (18)           |   89 | rhubarb (11)             |
|   40 | stone fruit (26)         |   65 | fig (17)                 |   90 | walnut (11)              |
|   41 | cranberry (24)           |   66 | guava (17)               |   91 | green tea (10)           |
|   42 | papaya (24)              |   67 | smooth (17)              |   92 | prune (10)               |
|   43 | berries (23)             |   68 | orange blossom (16)      |   93 | tobacco (10)             |
|   44 | butterscotch (23)        |   69 | rose (15)                |   94 | white grape (10)         |
|   45 | cinnamon (23)            |   70 | watermelon (15)          |   95 | bright (9)               |
|   46 | grape (23)               |   71 | berry (14)               |   96 | date (9)                 |
|   47 | balanced (22)            |   72 | cane sugar (14)          |   97 | spice (9)                |
|   48 | mandarin (22)            |   73 | clementine (14)          |   98 | baker's chocolate (8)    |
|   49 | melon (22)               |   74 | sugar cane (14)          |   99 | candied lemon (8)        |
|   50 | pear (22)                |   75 | tropical fruit (14)      |  100 | cherry cola (8)          |

Rank ordering uses retained normalized occurrence frequency descending and
normalized text ascending as the tie-break. Country prevalence is `NULL`
because roaster country is not source-asserted.

## Modifier probes

The six requested exact normalized probes behave as follows:

| Probe      | Occurrences | Documents | Publishers | Highest-count observed contexts                                      |
| ---------- | ----------: | --------: | ---------: | -------------------------------------------------------------------- |
| `bright`   |           9 |         9 |          9 | lemon (2); all other stored pairs occur once                         |
| `clean`    |          12 |        12 |         11 | floral (3), delicate (2), sweet (2)                                  |
| `juicy`    |          34 |        34 |         26 | caramel (4), cranberry (3), grapefruit (3), sweet (3), chocolate (3) |
| `jammy`    |           5 |         5 |          5 | floral (3); other stored pairs occur once                            |
| `tea-like` |           0 |         0 |          0 | no exact normalized probe occurrence                                 |
| `winey`    |           5 |         5 |          5 | all stored pairs occur once                                          |

The contexts include fruit references, floral language, sweet-associated
references, tactile language, and other modifiers. Those are surface-language
observations, not automatic concept-type assignments. The six ontology terms
remain candidate qualifiers in Round 2A; `winey` also has a distinct sensory
sense. No formula, intensity, coordinate, or automatic promotion was added.

## Co-occurrence and NPMI

The statistic layer stores 4,600 unordered normalized-expression pairs observed
within the same document. For each pair it records document co-occurrence count,
sample count, both directional conditional rates, and natural-log NPMI:

`NPMI(x,y) = PMI(x,y) / -ln(P(x,y))`

The denominator is the 2,474-document frozen sample. Of 4,600 stored pairs,
4,448 have positive NPMI and 152 have negative NPMI; the observed range is
`-0.2002667267` through `1.0`. Rare pairs can reach `1.0` from a single shared
document, so NPMI must always be read with co-occurrence and marginal document
counts. No pair is converted into `kb.concept_relation`.

## Stability diagnostics

At batch 16, top-25 set overlap with batch 15 was 25/25 and top-100 overlap was
98/100. A fixed-seed, 100-replicate document bootstrap compared top-five
co-occurrence neighbours for 173 expressions with document frequency at least
five. Final mean Jaccard was `0.3686790531` and median Jaccard was
`0.4285714286`; the median remained `0.4285714286` across cumulative batches
14–16. Consecutive-batch top-five-neighbour median Jaccard was `1.0` over 317
eligible expressions, but the weaker bootstrap result prevents a broad
stability claim.

Batch 16 still discovered 48 normalized expressions. The high-frequency head
is comparatively stable, while the vocabulary long tail and resampled
co-occurrence neighbourhoods are not converged.

## Type-prevalence boundary

The frozen statistic layer does not guess canonical type from surface form.
Under the deliberately narrow exact-expression resolution boundary, 1,866 of
5,564 retained occurrences resolve through exactly one current active
preferred or approved lexicalization; 3,698 remain explicitly unresolved.
This is occurrence coverage `0.33537023723939611790`; the unresolved share is
`0.66462976276060388210`. At the normalized-identity level, 57 of 1,713
identities resolve and 1,656 remain unresolved, for coverage
`0.03327495621716287215` and unresolved share
`0.96672504378283712785`.

Within that strict resolved subset, active composite references account for
seven occurrences (`0.0012580877` of all retained occurrences), and active
qualifiers account for zero. These are conservative exact-governance counts,
not an inferred corpus-wide type distribution. Normalized-phrase, trigram,
graph, and polysemous candidates do not satisfy the materialized resolution
boundary; in particular, `winey` remains unresolved rather than being forced
to one of its possible senses.

These counts are preserved in the frozen run
`resolution_run.firstbloom_a6cb002_pilot_v1.exact_v1` and its immutable
per-observation history. The current resolution projection is validated against
the latest frozen run; a later policy can add a new run without rewriting this
V1 receipt.
