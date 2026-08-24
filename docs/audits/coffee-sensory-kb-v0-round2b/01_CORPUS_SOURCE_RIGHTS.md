# Round 2B corpus source rights

Date assessed: 2026-08-24

Status: `RIGHTS_REVIEW_PASS=true`

## Decision boundary

Round 2B treats industry tasting notes as language observations, not objective
flavor labels or canonical sensory evidence. Public visibility, technical
crawlability, and a permissive `robots.txt` do not establish permission to
collect or redistribute content.

The source-policy matrix reviewed 15 candidates. One pinned repository source
was admitted for derived terms, eight sources were explicitly blocked, three
were limited to manual metadata review, and three remained unknown. The three
unknown rows have `source_blocked=true`, so the effective blocked count is 11;
the three manual-only rows also contributed no corpus content. No live site was
scraped.

The authoritative evidence is the
[source-rights matrix](../../../db/data/round2b/source_rights.tsv), the
[pinned-source manifest](../../../db/data/round2b/firstbloom_source_manifest.json),
the [Firstbloom attribution and boundary](../../../db/data/round2b/FIRSTBLOOM_ATTRIBUTION.md),
and the [generation receipt](../../../db/data/round2b/generation_receipt.json).

## Reviewed policies

| Source                        | Country             | Decision                          | Round 2B acquisition            | Rights evidence                                                                                                                                                                  |
| ----------------------------- | ------------------- | --------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Firstbloom Data               | Not source-asserted | `ALLOW_DERIVED_TERMS`             | Pinned repository snapshot only | [repository](https://github.com/alexcaza/firstbloom-data), [CC BY 4.0 grant](https://github.com/alexcaza/firstbloom-data/blob/a6cb0026d1af9642724793c799bbc48dc189ba35/LISCENSE) |
| Square Mile Coffee Roasters   | GB                  | `BLOCKED`                         | None                            | [terms](https://shop.squaremilecoffee.com/pages/terms-conditions)                                                                                                                |
| Proud Mary Coffee             | AU                  | `BLOCKED`                         | None                            | [terms](https://www.proudmarycoffee.com.au/pages/terms-and-conditions)                                                                                                           |
| Kurasu                        | JP                  | `BLOCKED`                         | None                            | [terms](https://kurasu.kyoto/policies/terms-of-service)                                                                                                                          |
| Counter Culture Coffee        | US                  | `BLOCKED`                         | None                            | [terms](https://counterculturecoffee.com/pages/terms-of-service)                                                                                                                 |
| Origin Coffee                 | GB                  | `BLOCKED`                         | None                            | [terms](https://www.origincoffee.co.uk/pages/terms-conditions)                                                                                                                   |
| Yardstick Coffee              | PH                  | `BLOCKED`                         | None                            | [terms](https://yardstickcoffee.com/policies/terms-of-service)                                                                                                                   |
| Common Man Coffee Roasters    | SG                  | `BLOCKED`                         | None                            | [terms](https://commonmancoffeeroasters.com/policies/terms-of-service)                                                                                                           |
| Father Coffee                 | ZA                  | `BLOCKED`                         | None                            | [terms](https://father.coffee/policies/terms-of-service)                                                                                                                         |
| Nomad Coffee                  | ES                  | `MANUAL_ONLY`                     | None                            | [legal notice](https://nomadcoffee.es/en/policies/legal-notice)                                                                                                                  |
| Market Lane Coffee            | AU                  | `MANUAL_ONLY`                     | None                            | [terms](https://marketlane.com.au/pages/terms-and-conditions)                                                                                                                    |
| Single O                      | AU                  | `MANUAL_ONLY`                     | None                            | [terms](https://singleo.com.au/pages/privacy-policy-terms-conditions)                                                                                                            |
| 49th Parallel Coffee Roasters | CA                  | `UNKNOWN` and effectively blocked | None                            | [terms](https://49thcoffee.com/pages/terms-of-service)                                                                                                                           |
| Tim Wendelboe                 | NO                  | `UNKNOWN` and effectively blocked | None                            | [terms and privacy](https://timwendelboe.no/en-no/pages/terms-privacy)                                                                                                           |
| Coffee Collective             | DK                  | `UNKNOWN` and effectively blocked | None                            | [terms](https://coffeecollective.dk/policies/terms-of-service)                                                                                                                   |

These decisions are versioned project-governance decisions for the intended
corpus use, not general legal opinions about the sources.

## Acquired source and attribution

The sole acquired source is [Firstbloom Data](https://github.com/alexcaza/firstbloom-data)
by Alex Caza, licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The input is pinned
to Git commit `a6cb0026d1af9642724793c799bbc48dc189ba35`; its individual input-file
hashes are recorded in the source manifest and generation receipt.

Firstbloom is a historical secondary aggregation. Its licence authorizes reuse
of the dataset as offered, but it does not make the observations sensory truth
or independently establish that every upstream roaster authorized every use.
Round 2B therefore applies the narrower `ALLOW_DERIVED_TERMS` boundary:

- structured source metadata, hashes, short admitted phrase fragments, and
  derived statistics may be stored with attribution;
- complete tasting-note fields, long commercial descriptions, and consumer
  reviews are not emitted or committed;
- `raw_text_allowed=false` even for Firstbloom;
- the legacy `evidence.license_policy.production_export_allowed` flag remains
  `false`, preserving the conservative raw-export boundary established by the
  metadata-only licence policy;
- the narrower Round 2B source-policy grant sets
  `derived_terms_redistribution_allowed=true`, while the reviewed matrix's
  `production_export_allowed=true` applies only to governed short derived terms
  and structured metadata. Neither flag authorizes export of excluded raw
  commercial text.

Consumer-review data is not read by the generator. Complete selected source
fields are globally hash-only, and fragments longer than 80 Unicode characters
are hash-only. The database stores `raw_text=NULL` for snapshot documents.

## Gate result

`CORPUS_SOURCE_COUNT=1`, `CORPUS_ALLOWED_SOURCE_COUNT=1`,
`CORPUS_BLOCKED_SOURCE_COUNT=11`, and `MANUAL_ONLY_SOURCE_COUNT=3`. The 215
publisher identities inside Firstbloom are sampling units under one shared
dataset policy; they are not 215 independently licensed acquisition sources.

The rights gate passes because only the one permitted, pinned snapshot was
used, attribution is preserved, raw commercial text is excluded, and every
blocked, unknown, or manual-only live source contributed zero acquired
documents.
