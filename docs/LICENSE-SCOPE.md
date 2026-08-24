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

## Research Boundary

The current sensory association ranges are project-curated drafts. They should
not be reused in a way that implies official measurement, formal cupping
authority, universal sensory truth, or direct derivation from WCR, SCA, UC
Davis, or commercial coffee datasets.
