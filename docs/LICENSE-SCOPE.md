# License Scope

Coffee Flavor Atlas uses layered licensing so software, original research
content, curated data, and third-party materials are not blurred together.

## MIT License

The root [LICENSE](../LICENSE) applies to project-authored software components:

- application source code;
- schemas;
- utilities;
- tests;
- configuration;
- build scripts;
- original software components.

## CC BY 4.0

[LICENSES/CC-BY-4.0.txt](../LICENSES/CC-BY-4.0.txt) applies to
project-authored research and curated content:

- research prose;
- original methodology documentation;
- original bilingual summaries;
- manually curated descriptor records;
- project-created data annotations;
- original diagrams that are explicitly marked as project-created.

Attribution should cite the repository and the exact release or commit used.

## TypeScript Data Files

Some TypeScript files contain both software structure and authored content.

- TypeScript wrappers, types, validation code, search utilities, sorting
  utilities, comparison utilities, and tests are MIT licensed.
- Project-authored descriptor text, bilingual summaries, aliases, editorial
  notes, and manually curated sensory association values are CC BY 4.0.
- Content quoted from or derived from third-party sources remains governed by
  the source material's own license or reuse terms.

## Third-Party Materials

The following are not automatically re-licensed by this repository's MIT or
CC BY 4.0 terms:

- third-party datasets;
- WCR materials;
- SCA materials;
- Cup of Excellence materials;
- fonts;
- icons;
- SVG libraries;
- images;
- dependencies;
- quoted source material.

See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and
[docs/ASSET-LICENSES.md](ASSET-LICENSES.md) for current asset and notice
records.

## Round 2B Corpus Layers

Round 2B keeps four licensing and provenance layers distinct:

- corpus-governance schemas, normalizers, retrieval functions, generators,
  migration tooling, and tests are project-authored software under MIT;
- project-authored sampling decisions, hash-only admission annotations,
  adjudications, audit rubrics, and audit prose are under CC BY 4.0;
- Firstbloom-derived product metadata and admitted short tasting-language
  observations retain Firstbloom's CC BY 4.0 terms and attribution;
- blocked-source policy metadata, URLs, non-content hashes, and rights receipts
  do not grant permission to acquire or redistribute the referenced source
  content.

Complete commercial tasting-note fields, long descriptions, consumer reviews,
and source-specific controlled vocabularies are outside the redistributable
pilot. A public database rebuild from committed migrations is reproducible;
regenerating those derived artifacts from upstream requires the separately
obtained, checksum-verified pinned source checkout.

## Round 3G evidence layers

Round 3G keeps its rights boundaries explicit:

- source-family, source-version, evidence-claim, review, expected-state and
  validation schemas are project-authored software under MIT;
- project-created source annotations, rights/privacy decisions, evidence
  interpretations, review dispositions and audit prose are under CC BY 4.0;
- `liberica_rata_summary_matrix.tsv` is a transformed, de-identified aggregate
  derived from Mendeley Data DOI `10.17632/m3n2gc4dv6.1` and retains the
  upstream CC BY 4.0 terms and attribution;
- the raw Liberica workbook is external-only and is not committed or included
  in the public-export boundary because it contains pseudonymous panelist
  initials; and
- Wiktionary revision JSON files contain only API metadata. They remain within
  the upstream CC BY-SA 4.0/GFDL attribution boundary and do not include entry
  definitions, translations or quotation corpora.

Admitting a source under an open license does not make its relationships
canonical, cross-source supported, bilingual reviewed or scientifically
generalizable. The database preserves source-local scope and independent-family
counting separately from redistribution rights.

## Research Boundary

The current sensory association ranges are project-curated drafts. They should
not be reused in a way that implies official measurement, formal cupping
authority, universal sensory truth, or direct derivation from WCR, SCA, UC
Davis, or commercial coffee datasets.
