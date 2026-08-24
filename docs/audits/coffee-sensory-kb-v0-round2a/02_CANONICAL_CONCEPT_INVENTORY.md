# Round 2A canonical concept inventory

Date: 2026-08-24

Status: frozen seed contract verified in two clean PostgreSQL 17 rebuilds

## Type and lifecycle totals

The sensory-attribute count is reported separately from all other concept
types.

| Concept type        |  Active | Candidate |   Total |
| ------------------- | ------: | --------: | ------: |
| Sensory attribute   |      92 |         8 |     100 |
| Category            |      20 |         0 |      20 |
| Composite reference |       1 |         0 |       1 |
| Qualifier           |       0 |         6 |       6 |
| Process entity      |       1 |         1 |       2 |
| Affective term      |       0 |         1 |       1 |
| **All concepts**    | **114** |    **16** | **130** |

`CANONICAL_COUNT_OUTSIDE_EXPECTED_RANGE=false`: the 92 active sensory
attributes fall within the expected 90--120 range. The eight candidates were
not promoted to pad the active inventory.

## Active sensory attributes

The groupings below are the independently authored project V0 organizational
projection. They are non-exclusive organizational aids, not universal sensory
dimensions, botanical taxonomy, ingredient claims, process causes, or copied
source-wheel placement. Each active attribute appears once in this counting
inventory; `sensory.metallic` also has a second project-scheme parent under
`category.chemical`.

| Audit grouping                                                         | Count | Active concept keys                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------------------------------- | ----: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Taste and oral sensation                                               |    13 | `sensory.sweet`, `sensory.sour`, `sensory.bitter`, `sensory.salty`, `sensory.astringent`, `sensory.drying`, `sensory.fullness`, `sensory.smooth_mouthfeel`, `sensory.oily_mouthfeel`, `sensory.creamy_mouthfeel`, `sensory.syrupy_mouthfeel`, `sensory.mouth_coating`, `sensory.metallic`                                                                                                                                   |
| Fruit, including project citrus/orchard/berry/tropical/dried subgroups |    22 | `sensory.grape`, `sensory.lemon`, `sensory.lime`, `sensory.orange`, `sensory.grapefruit`, `sensory.bergamot`, `sensory.apple`, `sensory.pear`, `sensory.peach`, `sensory.plum`, `sensory.cherry`, `sensory.pomegranate`, `sensory.strawberry`, `sensory.raspberry`, `sensory.blueberry`, `sensory.blackberry`, `sensory.banana`, `sensory.pineapple`, `sensory.mango`, `sensory.coconut`, `sensory.raisin`, `sensory.prune` |
| Floral                                                                 |     3 | `sensory.jasmine`, `sensory.rose`, `sensory.chamomile`                                                                                                                                                                                                                                                                                                                                                                      |
| Green and herbal                                                       |     5 | `sensory.fresh_grass`, `sensory.hay`, `sensory.green_vegetal`, `sensory.pea_pod`, `sensory.bell_pepper`                                                                                                                                                                                                                                                                                                                     |
| Tea                                                                    |     1 | `sensory.black_tea`                                                                                                                                                                                                                                                                                                                                                                                                         |
| Nut and seed                                                           |     4 | `sensory.almond`, `sensory.hazelnut`, `sensory.peanut`, `sensory.walnut`                                                                                                                                                                                                                                                                                                                                                    |
| Spice                                                                  |     7 | `sensory.cinnamon`, `sensory.clove`, `sensory.nutmeg`, `sensory.black_pepper`, `sensory.cardamom`, `sensory.ginger`, `sensory.anise`                                                                                                                                                                                                                                                                                        |
| Sweet and brown                                                        |     6 | `sensory.honey`, `sensory.brown_sugar`, `sensory.molasses`, `sensory.caramel`, `sensory.vanilla`, `sensory.butter`                                                                                                                                                                                                                                                                                                          |
| Cocoa and chocolate                                                    |     2 | `sensory.cocoa`, `sensory.dark_chocolate`                                                                                                                                                                                                                                                                                                                                                                                   |
| Grain and baked                                                        |     4 | `sensory.malt`, `sensory.cereal_grain`, `sensory.baked_bread`, `sensory.toast`                                                                                                                                                                                                                                                                                                                                              |
| Roast                                                                  |     6 | `sensory.roasted_nut`, `sensory.roasted_character`, `sensory.smoky`, `sensory.burnt`, `sensory.ash`, `sensory.tobacco`                                                                                                                                                                                                                                                                                                      |
| Earth and wood                                                         |     8 | `sensory.earthy`, `sensory.damp_soil`, `sensory.mushroom`, `sensory.woody`, `sensory.cedar`, `sensory.dusty`, `sensory.musty`, `sensory.moldy`                                                                                                                                                                                                                                                                              |
| Paper and storage                                                      |     3 | `sensory.paper`, `sensory.cardboard`, `sensory.stale`                                                                                                                                                                                                                                                                                                                                                                       |
| Chemical references, excluding already-counted `metallic`              |     4 | `sensory.rubber`, `sensory.petroleum`, `sensory.phenolic`, `sensory.sulfurous`                                                                                                                                                                                                                                                                                                                                              |
| Fermentation-associated character                                      |     4 | `sensory.fermented_character`, `sensory.wine_like_character`, `sensory.acetic_vinegar`, `sensory.alcoholic`                                                                                                                                                                                                                                                                                                                 |

## Candidate sensory attributes

| Concept key               | Project placement                                                           | Why it is not active                                                                                          |
| ------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `sensory.pink_grapefruit` | Deliberately unplaced; retained separately from active `sensory.grapefruit` | The reviewed evidence supports the broader grapefruit scope, not the narrower candidate identity              |
| `sensory.blackcurrant`    | Berry                                                                       | Exact use was not verified in the checked article text, and no exact-term supplementary evidence was verified |
| `sensory.orange_blossom`  | Floral                                                                      | Exact use was not verified in the checked article text, and no exact-term supplementary evidence was verified |
| `sensory.mint`            | Green/herbal                                                                | Exact use was not verified in the checked article text, and no exact-term supplementary evidence was verified |
| `sensory.eucalyptus`      | Green/herbal                                                                | Exact use was not verified in the checked article text, and no exact-term supplementary evidence was verified |
| `sensory.lemongrass`      | Green/herbal                                                                | Exact use was not verified in the checked article text, and no exact-term supplementary evidence was verified |
| `sensory.green_tea`       | Green/herbal and tea candidate parents                                      | Exact use was not verified in the checked article text, and no exact-term supplementary evidence was verified |
| `sensory.leather`         | Earth/wood                                                                  | Exact use was not verified in the checked article text, and no exact-term supplementary evidence was verified |

These are project-authored proposals, not representations of externally
defined concepts. Their candidate scheme nodes and edges remain outside current
active scheme views.

## Project categories

The 20 active categories are `category.taste_oral`, `category.fruit`,
`category.citrus`, `category.orchard_fruit`, `category.berry`,
`category.tropical_fruit`, `category.dried_fruit`, `category.floral`,
`category.green_herbal`, `category.tea`, `category.nut_seed`,
`category.spice`, `category.sweet_brown`, `category.cocoa_chocolate`,
`category.grain_baked`, `category.roast`, `category.earth_wood`,
`category.paper_storage`, `category.fermentation`, and `category.chemical`.

## Other governed concept types

| Type/status                | Concept keys                                                                                                         | Boundary                                                                                              |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Active composite reference | `composite.earl_grey`                                                                                                | A consumer reference distinct from both bergamot and black tea; it is not their synonym               |
| Candidate qualifiers       | `qualifier.bright`, `qualifier.clean`, `qualifier.juicy`, `qualifier.tea_like`, `qualifier.winey`, `qualifier.jammy` | Contextual modifiers without formula, intrinsic score, vector, or projection coordinate               |
| Active process entity      | `process.fermentation`                                                                                               | Process metadata, distinct from perceived fermented character                                         |
| Candidate process entity   | `process.anaerobic_fermentation`                                                                                     | A process-language proposal that asserts neither protocol equivalence nor resulting sensory character |
| Candidate affective term   | `affective.pleasant`                                                                                                 | Evaluative language excluded from descriptive sensory projections                                     |

## Lexicalization policy

The seed supplies one preferred English label per concept and retains only four
non-preferred mappings from the Round 1 fixtures: approved variants for
`pink-grapefruit`, `earl grey tea`, and `tea like`, plus the explicit
polysemous use of `winey`. `winey` maps to both the candidate qualifier and the
active sensory character, while retrieval declines to force the ambiguous form
to one sense. `Earl Grey` resolves to its composite identity, not to bergamot.

The rebuilt database contains 134 lexical expressions and 134 current
lexicalizations, including the deliberately unmatched `meteor fruit` retrieval
fixture. Comprehensive Simplified Chinese population is outside Round 2A; the
`zh-Hans` architecture remains intact.

## Stable dimensions

The six existing dimensions remain unchanged:

- `taste.sweetness`
- `taste.sourness_acidity`
- `taste.bitterness`
- `taste.saltiness`
- `tactile.body_fullness`
- `tactile.drying_astringency`

Round 2A creates six corresponding nonnumeric concept links. No concept stores
an intrinsic coordinate, score, intensity, desirability, or empirical PCA/MDS
value. Floral, fruity, roasted, and nutty are not promoted to universal axes.

## Description authorship

Every concept description is concise, non-evaluative project prose. External
evidence supports admission or boundary review but is not used as definition
text. Category descriptions explicitly disclaim exclusivity, taxonomy,
ingredient presence, causality, or universal source placement where relevant.
