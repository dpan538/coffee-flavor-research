# Round 3J source rights and versions

This audit records the rights state actually established at acquisition time.
`PUBLIC_*` and `MODEL_RESEARCH_USE_*` statuses are admission controls, not
claims about what might become permissible after additional review. Public web
access alone never sets them to allowed.

## Authorized file-audit candidates

| Candidate                     | Version and access                                                   | Observed rights                                                                                                                    | Privacy finding                                                                        | Public corpus / raw public / model research                                                      | Decision                                                                                                                                                                                                      |
| ----------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Liang full-immersion          | Dryad DOI `10.5061/dryad.v15dv423h`; record 124603 inaccessible      | CC0 1.0 appeared in preregistered metadata, but no payload/version could be retrieved                                              | No payload to review                                                                   | Not allowed / not allowed / not allowed                                                          | Blocked on retrievable source version                                                                                                                                                                         |
| Golovinsky electrochemical    | Zenodo record `20840464`, DOI `10.5281/zenodo.20840464`, version 1.1 | Structured field: CC BY 4.0; record description: CC BY-NC 4.0 and non-commercial research only                                     | Sensory workbook exposes direct panelist names                                         | Not allowed / not allowed / not allowed                                                          | Quarantine for license conflict and privacy                                                                                                                                                                   |
| Bichlmaier mozambioside       | Mendeley DOI `10.17632/xzjppbmn58.1`, version 1                      | CC BY 4.0; file-level segregation remains required                                                                                 | Human sensory and DoT workbooks contain participant and TAS2R43-style genotype fields  | Not allowed / not allowed / not allowed in current unsplit state                                 | Quarantine sensitive workbooks; safe files lack source-local sensory outcomes                                                                                                                                 |
| `guchengf` reviews            | Author archive snapshot `2025-posts-snapshot-20260826`               | Site states CC BY 4.0 unless separately licensed; acquired pages repeat the license boundary; author-main-prose boundary completed | Public authorship only; no participant dataset in the acquired pages                   | Allowed with CC BY attribution / allowed with CC BY attribution / allowed with CC BY attribution | Retain bounded raw snapshot; derived 22 candidates exclude images, figcaptions, ratings, metadata, footer, site shell, and separately marked material; candidates remain unimported and not sampling eligible |
| Xian Zhang zero-price reviews | Mendeley DOI `10.17632/8mmw6wb26r.2`, version 2                      | CC BY 4.0; deidentification and file-purpose review remain required                                                                | Participant IDs, demographics, experimental variables, and human free text are present | Not allowed / not allowed / not allowed in current raw state                                     | Do not publish or admit participant workbooks; no zh-Hans gain                                                                                                                                                |

The Golovinsky conflict cannot be resolved by preferring the more permissive
structured field. The narrower human-readable statement controls the current
decision until the depositor or repository supplies an unambiguous grant.

## Metadata-only candidates

| Execution batch | Candidates               | Controlling rights/access state                                                         | Current public corpus / raw public / model research status                    |
| --------------- | ------------------------ | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `R3J-AQ-002`    | Carvalho canephora       | Article CC BY-NC-ND 4.0; dataset license/version unresolved; private share link         | Not allowed / not allowed / not allowed                                       |
| `R3J-AQ-002`    | Münchow roasting         | CC BY 4.0 article aggregates; no raw panel repository                                   | Not allowed / not allowed / not allowed for a source-local raw corpus         |
| `R3J-AQ-002`    | Juravle citizen science  | CC BY 4.0 article; underlying data rights not public and data available only by request | Not allowed / not allowed / not allowed                                       |
| `R3J-AQ-002`    | Birke Rune acids         | Open-access article; raw-data license unverified and data on request                    | Not allowed / not allowed / not allowed                                       |
| `R3J-AQ-003`    | Open Food Facts          | ODbL/DbCL/share-alike layers; no immutable coffee snapshot selected                     | Not allowed / not allowed / not allowed in the current unpartitioned state    |
| `R3J-AQ-003`    | Beans with Beanie        | All rights reserved; commercial consent and upstream roaster rights unresolved          | Not allowed / not allowed / not allowed                                       |
| `R3J-AQ-003`    | Open Coffee Hub          | No open data/content license surfaced; upstream chain unresolved                        | Not allowed / not allowed / not allowed                                       |
| `R3J-AQ-003`    | Cherrybook               | Proprietary terms prohibit automated access; upstream copy rights unresolved            | Not allowed / not allowed / not allowed                                       |
| `R3J-AQ-004`    | Duran brewing note       | CC BY-NC 4.0                                                                            | Not allowed / not allowed / not allowed for the unrestricted corpus           |
| `R3J-AQ-004`    | Slegetank summary        | CC BY-SA 4.0 site; source-book derivative rights unresolved                             | Not allowed / not allowed / not allowed                                       |
| `R3J-AQ-004`    | Hans polyphenols         | CC BY 4.0 article; research reference rather than tasting-language corpus               | Not allowed / not allowed / not allowed as a corpus source at this checkpoint |
| `R3J-AQ-004`    | OSF flavour descriptions | Project file license not surfaced; stimuli mix third-party and constructed text         | Not allowed / not allowed / not allowed                                       |

No metadata-only candidate was downloaded, hashed, imported, or counted as a
new source family. Reported article participants, samples, roasters, products,
or catalog totals remain contextual metadata rather than corpus rows.

## Admission rule

A future candidate may enter a frozen corpus only when its exact source
version, file hashes, license scope, upstream provenance, privacy state,
public-corpus status, raw-public-release status, and model-research-use status
are explicit. The acquisition authorization flag in the source-candidate
register is never a substitute for those checks.
