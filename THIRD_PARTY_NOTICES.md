# Third-Party Notices

Third-party materials are not automatically covered by this repository's MIT
or CC BY 4.0 licenses. Dependencies, fonts, icons, source frameworks, datasets,
and referenced research materials keep their own licenses and reuse limits.

Detailed asset records are maintained in
[`docs/ASSET-LICENSES.md`](docs/ASSET-LICENSES.md).

## Public Attribution Required

The current visual asset spike includes six SVG files from Game-icons.net under
CC BY 3.0. Attribution is required for public use:

- Jasmine by Delapouite, Game-icons.net, CC BY 3.0.
- Lemon by Delapouite, Game-icons.net, CC BY 3.0.
- Berries bowl by Delapouite, Game-icons.net, CC BY 3.0.
- Chocolate bar by Rihlsul, Game-icons.net, CC BY 3.0.
- Hot spices by Lorc, Game-icons.net, CC BY 3.0.
- Cheese wedge by Lorc, Game-icons.net, CC BY 3.0.

## Font Packages

The app uses Fontsource packages for Bodoni Moda, IBM Plex Sans, IBM Plex Mono,
Noto Sans SC, and Noto Serif SC. The installed packages report `OFL-1.1`
licensing. Font files are installed through npm and are not committed directly
as vendored binaries in this repository.

## Firstbloom Data

The Round 2B historical industry-language pilot derives governed metadata and
short tasting-language observations from **Firstbloom Data** by Alex Caza,
licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The source is pinned to commit
`a6cb0026d1af9642724793c799bbc48dc189ba35` of
<https://github.com/alexcaza/firstbloom-data>. Transformations include
deterministic sampling, rights-boundary redaction, independent project
admission review by two Codex-assisted curation passes, phrase normalization,
duplicate review, and aggregate statistics. These passes are not represented
as human reviewers.

The repository does not include Firstbloom consumer reviews, roaster
descriptions, complete tasting-note fields, or source-specific controlled
hierarchies. Rejected, non-English, narrative, uncertain, and over-length
observations are represented only by non-content receipts. The source is a
historical secondary aggregation; its licensed language observations are not
objective sensory truth and do not establish global or current-market
representativeness. The detailed attribution and transformation boundary is in
[`db/data/round2b/FIRSTBLOOM_ATTRIBUTION.md`](db/data/round2b/FIRSTBLOOM_ATTRIBUTION.md).

## NPM Dependencies

Runtime and development dependencies retain their package licenses as recorded
in `package-lock.json` and each package's own metadata. This file is a summary,
not a replacement for dependency license review before formal release.

## Materials Not Re-Licensed Here

- WCR materials.
- SCA materials.
- Cup of Excellence materials.
- UC Davis dataset content.
- Font packages and font files.
- Game-icons.net SVGs.
- Firstbloom Data and its derived source observations.
- NPM dependencies.
- Any quoted or referenced third-party source material.

## Unconfirmed Materials

No additional unconfirmed image, SVG, font, dataset, DOCX, PDF, or binary asset
is intentionally included in this first public baseline.
