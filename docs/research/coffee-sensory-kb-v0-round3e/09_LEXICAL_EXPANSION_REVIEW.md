# Lexical expansion review

Round 3E preserves 215 expression occurrences from 46 versioned corpus
documents. They resolve to 134 normalized expressions and 107 mapping
candidates. Every mapping remains source-local and lifecycle governed; none was
promoted into the active ontology.

The generated register is
`db/data/round3e/generated/lexical_mapping_candidates.tsv`. Each row retains
the raw source phrase, normalized expression, candidate mapping, evidence key,
review state, scope and ambiguity note. Normalization never overwrites the raw
phrase.

## Evidence admitted

| Source                            | Lexical contribution                                                   | Boundary                                                                    |
| --------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Wikidata fixed-revision snapshot  | English and Chinese labels/aliases for 14 preparation entities         | entity labels are lexical evidence, not proof of sensory or C0 equivalence  |
| USDA FNDDS fixed API page         | 32 admitted English coffee-beverage descriptions with product metadata | food descriptions are preparation/product language, not tasting outcomes    |
| Round 2B Firstbloom frozen corpus | historical tasting-note expressions                                    | retained for comparison; source-concentrated and not a new Round 3E capture |

The Wikidata snapshot is governed by its
[CC0 data license](https://www.wikidata.org/wiki/Wikidata:Licensing), and the
USDA source is governed by the
[FoodData Central data policy](https://fdc.nal.usda.gov/data-documentation.html).
Both captures are immutable or version-addressed in the manifest.

## Curation decisions

- Orthographic and multilingual variants remain separate occurrences linked by
  a candidate mapping, not asserted synonyms.
- `espresso`, `Americano`, `long black`, cold-coffee, milk-coffee and stovetop
  terms are candidate preparation expressions only.
- Broad, narrower and composite phrases retain their source wording. Coverage
  is not increased by assigning ambiguous expressions such as `iced coffee` or
  `white coffee` to a single C0 category.
- Frequency is a prioritization signal for review only. A database trigger and
  negative test reject automatic activation of recurrent terms.
- Model/lexical candidates remain `RESEARCH_REVIEWED` or `CANDIDATE`; no
  embedding or model result exists.

`NEW_LEXICAL_MAPPING_COUNT=107`. Of 215 occurrences, 122 remain at candidate
review state. They require source-specific semantic review, and Chinese terms
also require Mainland register and experiential-equivalence review.
