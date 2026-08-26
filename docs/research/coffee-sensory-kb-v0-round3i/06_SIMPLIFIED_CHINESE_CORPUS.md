# Round 3I Simplified-Chinese corpus

Round 3I admits two independent, source-authored Simplified-Chinese coffee-sensory families. The frozen corpus contains eight scoped documents, 249 unique normalized expressions, and 253 occurrences. No expression is a project translation or machine translation.

## Source-local counts

| Source family                | Documents | Occurrences | Unique expressions | Cross-source normalized overlap |
| ---------------------------- | --------: | ----------: | -----------------: | ------------------------------: |
| Junru Zhang, `Tasting Notes` |         7 |         230 |                226 |                               0 |
| 泠時月, `首次冷萃记录`       |         1 |          23 |                 23 |                               0 |
| Total                        |         8 |         253 |                249 |                               0 |

The families have different upstream authorship, publication sites, frozen versions, and document structures. A shared CC BY license does not make them one origin.

| Gate                                                   | Target | Result | Decision |
| ------------------------------------------------------ | -----: | -----: | -------- |
| Independent source-authored `zh-Hans` sensory families |      2 |      2 | PASS     |
| Preferred unique source-authored `zh-Hans` expressions |    200 |    249 | PASS     |

## Expression roles

Roles are editorial navigation labels, not universal sensory equivalence classes. Unique-expression counts differ from occurrence counts when a source repeats a phrase.

| Role                        | Unique expressions | Occurrences |
| --------------------------- | -----------------: | ----------: |
| Sensory attribute           |                 69 |          70 |
| Aroma                       |                 63 |          64 |
| Basic taste                 |                 63 |          64 |
| Composite sensory phrase    |                 21 |          21 |
| Texture or body             |                 12 |          13 |
| Consumer metaphor           |                 10 |          10 |
| Unresolved sensory language |                  6 |           6 |
| Sensory qualifier           |                  5 |           5 |
| Total                       |                249 |         253 |

An unresolved role preserves a genuinely sensory source phrase whose narrower placement is not defensible. It does not authorize a model feature, translation equivalence, or descriptor merge.

## Junru Zhang scope

The admitted page is [`Tasting Notes`](https://zhangdeweb.site/2025/03/06/coffee/index.html), published in 2025. Its exact repository state is git commit `dc5d02885c599df207f6bbd8c2bbc4009a4303e8` and blob `f757d6f40372e33b4d7edb96ec4af69fed237f02`. The 45,613-byte HTML source has SHA-256 `19c8cce17bf4f97f8354d29a79e7e1e860be4ef8422a8ce65d479e91545dc3c4`.

Only the author's overview and personal-feeling sensory passages for seven coffee blocks are admitted. Reference-flavor package copy, alcohol blocks, images, theme assets, and interface text are excluded. The page footer licenses posts under CC BY 4.0 unless otherwise stated.

## 泠時月 scope

The admitted page is [`首次冷萃记录`](https://rinzemoon.top/article/articles/LengCui), dated 2026-04-25. The frozen response is 26,331 bytes, has ETag `W/"66db-zkjFNR3Mqp1vGFeK5G55s3we/4U"`, and has SHA-256 `bfefe1bba5efbeb508e87f4ea4a45d77adf49683e0b0fb606ee208f0e12a2f7f`.

Only the author's personal cold-brew sensory account is admitted. Appearance-only content, AI advice, milk-preparation context, comments, contact or security metadata, avatars, images, a friend remark, and the site shell are excluded. The page footer states CC BY 4.0 and requests retained attribution.

## Rights and privacy

Both source annotations record `ALLOW` for all seven dimensions:

| Dimension                           | Junru Zhang | 泠時月 |
| ----------------------------------- | ----------- | ------ |
| `raw_text_internal_use`             | ALLOW       | ALLOW  |
| `raw_text_public_redistribution`    | ALLOW       | ALLOW  |
| `derived_expression_internal_use`   | ALLOW       | ALLOW  |
| `derived_expression_public_release` | ALLOW       | ALLOW  |
| `derived_counts_internal_use`       | ALLOW       | ALLOW  |
| `derived_counts_public_release`     | ALLOW       | ALLOW  |
| `model_research_use`                | ALLOW       | ALLOW  |

The public export state is `PUBLIC_RAW` only for the reviewed, source-authored sensory expressions and provenance associated with the eight scoped documents. It does not extend to excluded passage material or whole-page republication. Attribution, a CC BY 4.0 link, change indication, and no suggestion of endorsement remain required. Public author identity is retained; no private-person identity, comment author, contact detail, or security metadata is exported.

## Frozen artifact receipts

| Artifact                               | Rows or role                  | SHA-256                                                            |
| -------------------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| `zh_hans/language_documents.tsv`       | eight scoped documents        | `431c79beacb98c277cf1c900678d95b3c58471038fbf848913ba4aa224cc89af` |
| `zh_hans/language_expressions.tsv`     | 249 unique expressions        | `de9a51eb61bc410a5742c456d99a804939d709f4e52aea22f651f703642e1e7b` |
| `zh_hans/language_occurrences.tsv`     | 253 occurrences               | `5b2ce6885721e9a328691c89e270c9a4629b73991fa661c31311c1984580f5c1` |
| `zh_hans/language_source_families.tsv` | two families                  | `96d927936d22ddacc40763c424d3335b72277c1090d7dc2997622922b44c8092` |
| `zh_hans/language_sources.tsv`         | rights and source annotations | `988983cd90f482499233cc563c480a27530e145e95566fc71e67c54304c16d8b` |

These records expand multilingual observation coverage. They do not establish preferred translations, cultural universals, or Simplified-Chinese labels for the 130-concept atlas.
