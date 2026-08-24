# Round 2A source and rights matrix

Date assessed: 2026-08-24

Status: `RIGHTS_REVIEW_PASS=true`

## Rights rule

The source record, source version, licence policy, retrieval date, locator, and
intended provenance use are stored separately. A visible source label or
bibliographic record is never treated as permission to redistribute source
content. Only the independently authored project ontology has
`production_export_allowed=true`.

No source definition, reference preparation, intensity, score, full protected
vocabulary, proprietary form, wheel layout, or source hierarchy is copied.
Descriptions and canonical organization are project-authored. External rows
record bibliographic metadata, conservative evidence locators, and admission
or scope support only.

## Round 2A matrix

All source versions use `retrieved_on=2026-08-24`. Rights labels below record
the repository's conservative policy decision for the identified version; they
are not a general legal opinion about other editions or uses.

| Source/version                                           | Primary locator                                                                                                             | Rights policy                                                                                 | Canonical use                                                                                                                                                       | Production export |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| Coffee Sensory Knowledge Base V0 Round 2A, `2026-08-24`  | `db/010_canonical_ontology_seed.sql`                                                                                        | Project content layer, CC BY 4.0; public; verified                                            | Independent concept scope, descriptions, lexical mappings, canonical relations, and project scheme                                                                  | Yes               |
| Chambers et al. (2016), version of record                | [Wiley DOI page](https://onlinelibrary.wiley.com/doi/10.1111/joss.12237)                                                    | CC BY-NC 4.0; metadata-only; verified                                                         | Lexicon-inclusion/admission evidence; no definitions, references, intensities, or full vocabulary                                                                   | No                |
| Carvalho et al. (2025), version of record                | [Scientific Reports article](https://www.nature.com/articles/s41598-025-99921-w)                                            | CC BY-NC-ND 4.0; metadata-only; verified; derivatives, commercial use, and machine use closed | Reported-use and scope evidence only; no wheel or source organization                                                                                               | No                |
| Ledezma, Sartori, and Tomasino (2025), version of record | [Wiley DOI page](https://onlinelibrary.wiley.com/doi/10.1002/fsn3.71278)                                                    | Rights unconfirmed; metadata-only; all reuse gates closed                                     | Reported-use locator only                                                                                                                                           | No                |
| Seninde and Chambers (2020), version of record           | [Beverages article](https://www.mdpi.com/2306-5710/6/3/44)                                                                  | CC BY 4.0 article; public; verified; evidence-only project policy                             | Cross-source scope evidence                                                                                                                                         | No                |
| Zhang et al. (2019), version of record                   | [Frontiers article](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2019.02621/full)               | CC BY 4.0 article; public; verified; evidence-only project policy                             | Processing-context scope evidence                                                                                                                                   | No                |
| Muenchow et al. (2020), version of record                | [Beverages article](https://www.mdpi.com/2306-5710/6/2/29)                                                                  | CC BY 4.0 article; public; verified; evidence-only project policy                             | Roast and brown-note scope evidence                                                                                                                                 | No                |
| Batali et al. (2022), version of record                  | [Foods article](https://www.mdpi.com/2304-8158/11/16/2440)                                                                  | CC BY 4.0 article; public; verified; evidence-only project policy                             | Trained-panel reported-use evidence                                                                                                                                 | No                |
| Bollen et al. (2024), version of record                  | [Frontiers article](https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1382976/full) | CC BY 4.0 article; public; verified; evidence-only project policy                             | Narrow reported-use/scope evidence; no third-party taxonomy imported                                                                                                | No                |
| Williams, de Andrade, and Liu (2023), version of record  | [Wiley DOI page](https://onlinelibrary.wiley.com/doi/10.1111/joss.12886)                                                    | CC BY-NC 4.0; metadata-only; verified                                                         | Mouthfeel scope evidence; published character wheel not copied                                                                                                      | No                |
| World Coffee Research Sensory Lexicon 2.0, public page   | [WCR resource page](https://worldcoffeeresearch.org/resources/sensory-lexicon)                                              | Personal-use/reuse-restricted; metadata-only; verified                                        | Flat, source-local partial scheme of the 24 labels expressly enumerated on the landing page; no definitions, references, intensities, full vocabulary, or hierarchy | No                |
| SCA Coffee Value Assessment, page retrieved 2026-08-24   | [SCA CVA page](https://sca.coffee/value-assessment)                                                                         | All-rights-reserved project policy; metadata-only; verified                                   | Method and standards context only; no forms or glossary imported                                                                                                    | No                |
| ISO 18794:2025, Edition 2                                | [ISO catalogue page](https://www.iso.org/standard/87695.html)                                                               | No-reproduction/no-machine-use project policy; metadata-only; verified                        | Standard metadata only; no standard text imported                                                                                                                   | No                |

## Source-version governance

Each source version is immutable once referenced. A changed edition requires a
new `evidence.source_version` and, where applicable, a new source-specific
scheme. Deleting a source or source version that supports historical evidence
is prohibited by restrictive foreign keys and covered by negative tests.

The WCR partial scheme is an evidence artifact, not the canonical ontology. SCA
and ISO records provide formal-method context only and do not create canonical
concepts or relations. The peer-reviewed articles support admission or scope;
their wording and organization do not become project definitions or canonical
hierarchy.

## Inherited Round 1 fixtures

The database also retains the independently authored Round 1 project smoke
source and a restricted synthetic fixture. They remain test/audit fixtures,
not external canonical evidence. Migration `010` assigns the old smoke concept
support rows the controlled `project_authorship` role instead of interpreting
their legacy free text.

## Open rights item

The applicable reuse licence for the Ledezma article was not verified from the
publisher page during this review. Its policy therefore remains
`rights_status=unknown`, `access_class=metadata_only`, and
`production_export_allowed=false`, with all reuse permissions closed. This
does not authorize source-content use; it preserves only bibliographic and
evidence-link metadata. Any future reuse requires a fresh rights review.

Both clean PostgreSQL rebuilds confirmed that every governed source version
resolves to its intended licence policy and that no restricted external source
is marked production-exportable. The 47-check Round 2A validation contract had
zero violations in both builds.
