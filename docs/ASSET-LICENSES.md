# Asset Licenses

This file records visual and font assets used or evaluated by the project. It
does not replace upstream license terms.

The first representational SVG spike uses six candidates from Game-icons.net.
Game-icons publishes these graphics under CC BY 3.0. Attribution is required.
These files are stored under `public/vendor/game-icons/` for local prototype
use.

No Google Images, Pinterest, Dribbble, Behance, unclear SVG Repo assets, or
unverified image downloads are used.

| Repository path                              | Asset/component              | Author/project                   | Original source                                           | License                        | Attribution required                     | Modified      | Notes                                                                  |
| -------------------------------------------- | ---------------------------- | -------------------------------- | --------------------------------------------------------- | ------------------------------ | ---------------------------------------- | ------------- | ---------------------------------------------------------------------- |
| `public/favicon.svg`                         | Project favicon              | Coffee Flavor Atlas project      | Project-created                                           | MIT for software interface use | No                                       | Yes           | Simple original interface mark.                                        |
| `public/vendor/game-icons/jasmine.svg`       | Jasmine icon                 | Delapouite / Game-icons.net      | <https://game-icons.net/1x1/delapouite/jasmine.html>      | CC BY 3.0                      | Yes                                      | No path edits | Framed by the Atlas specimen UI.                                       |
| `public/vendor/game-icons/lemon.svg`         | Lemon icon                   | Delapouite / Game-icons.net      | <https://game-icons.net/1x1/delapouite/lemon.html>        | CC BY 3.0                      | Yes                                      | No path edits | Framed by the Atlas specimen UI.                                       |
| `public/vendor/game-icons/berries-bowl.svg`  | Berries bowl icon            | Delapouite / Game-icons.net      | <https://game-icons.net/1x1/delapouite/berries-bowl.html> | CC BY 3.0                      | Yes                                      | No path edits | Candidate for `red-berries`; recognizability is medium.                |
| `public/vendor/game-icons/chocolate-bar.svg` | Chocolate bar icon           | Rihlsul / Game-icons.net         | <https://game-icons.net/1x1/rihlsul/chocolate-bar.html>   | CC BY 3.0                      | Yes                                      | No path edits | Candidate for `dark-chocolate`.                                        |
| `public/vendor/game-icons/hot-spices.svg`    | Hot spices icon              | Lorc / Game-icons.net            | <https://game-icons.net/1x1/lorc/hot-spices.html>         | CC BY 3.0                      | Yes                                      | No path edits | Cinnamon-adjacent first candidate; not a final settled cinnamon asset. |
| `public/vendor/game-icons/cheese-wedge.svg`  | Cheese wedge icon            | Lorc / Game-icons.net            | <https://game-icons.net/1x1/lorc/cheese-wedge.html>       | CC BY 3.0                      | Yes                                      | No path edits | Candidate for the boundary descriptor `cheese`.                        |
| `package.json` / npm install                 | Bodoni Moda via Fontsource   | Fontsource / Bodoni Moda project | <https://fontsource.org/fonts/bodoni-moda>                | OFL-1.1                        | No public UI attribution required by OFL | No            | Installed from npm, not committed as vendored font binaries.           |
| `package.json` / npm install                 | IBM Plex Sans via Fontsource | Fontsource / IBM Plex project    | <https://fontsource.org/fonts/ibm-plex-sans>              | OFL-1.1                        | No public UI attribution required by OFL | No            | Installed from npm, not committed as vendored font binaries.           |
| `package.json` / npm install                 | IBM Plex Mono via Fontsource | Fontsource / IBM Plex project    | <https://fontsource.org/fonts/ibm-plex-mono>              | OFL-1.1                        | No public UI attribution required by OFL | No            | Installed from npm, not committed as vendored font binaries.           |
| `package.json` / npm install                 | Noto Sans SC via Fontsource  | Fontsource / Noto project        | <https://fontsource.org/fonts/noto-sans-sc>               | OFL-1.1                        | No public UI attribution required by OFL | No            | Installed from npm, not committed as vendored font binaries.           |
| `package.json` / npm install                 | Noto Serif SC via Fontsource | Fontsource / Noto project        | <https://fontsource.org/fonts/noto-serif-sc>              | OFL-1.1                        | No public UI attribution required by OFL | No            | Installed from npm, not committed as vendored font binaries.           |

## Evaluation Notes

- Recognizability: strong for jasmine, lemon, chocolate, and cheese; medium for
  red berries and cinnamon.
- Style consistency: medium because the icons share a library but vary by
  author and path density.
- Animation fit: good for bloom, cluster, fracture, vapor, and bubble motion
  families.
- Black-and-white fit: strong enough for the editorial direction.

Before expanding to all 24 descriptors, review whether a single icon library
can support the full set without losing recognizability or creating excessive
attribution complexity.

## Research data and metadata

These are research artifacts rather than visual assets, but they are listed
here so the repository has one complete third-party material inventory.

| Repository path                                                                                                  | Asset/component                        | Author/project                                            | Original source                                                                               | License                        | Attribution required            | Modified | Notes                                                                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------- | -------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `db/data/round3g/liberica_rata_summary_matrix.tsv`                                                               | De-identified aggregate RATA summary   | Lita Meilina; Rangganis Ulya Auliya; Niken Widya Palupi   | Mendeley Data v1, DOI [10.17632/m3n2gc4dv6.1](https://doi.org/10.17632/m3n2gc4dv6.1)          | CC BY 4.0                      | Yes                             | Yes      | Ten aggregate summary rows transcribed from `RATA Test!A158:J168`; upstream workbook excluded from public export because it contains pseudonymous panelist initials.             |
| `db/data/round3g/enwiktionary_revision_metadata.json`                                                            | English Wiktionary revision metadata   | Wiktionary contributors / Wikimedia Foundation            | English Wiktionary MediaWiki Action API                                                       | CC BY-SA 4.0 and GFDL boundary | Yes if reused with page content | Yes      | Metadata only: page/revision IDs, timestamps and missing-title state; no definitions or quotations.                                                                              |
| `db/data/round3g/zhwiktionary_revision_metadata.json`                                                            | Chinese Wiktionary revision metadata   | Wiktionary contributors / Wikimedia Foundation            | Chinese Wiktionary MediaWiki Action API                                                       | CC BY-SA 4.0 and GFDL boundary | Yes if reused with page content | Yes      | Metadata only; counted in the same source family as English Wiktionary and not as bilingual review.                                                                              |
| `db/data/round3j/raw/candidate.r3j.regional.latam-br-mfact-consumer-sensory-2017/article-v1-2017/mfact_2017.pdf` | MFACT consumer sensory article         | Paulo César Ossani et al. / Universidade Federal do Ceará | UFLA repository; DOI [10.5935/1806-6690.20170010](https://doi.org/10.5935/1806-6690.20170010) | CC BY 4.0                      | Yes                             | No       | Version-of-record PDF retained for hash-bound aggregate extraction; participant data, forms, and correspondence details are excluded from derived outputs.                       |
| `db/data/round3j/raw/candidate.r3j.regional.latam-br-ufla-consumer-cata-2021/article-vor-2021/bressani_2021.pdf` | Specialty-coffee consumer CATA article | Ana Paula Pereira Bressani et al. / SciELO                | SciELO version of record; DOI [10.1590/fst.30720](https://doi.org/10.1590/fst.30720)          | CC BY 4.0                      | Yes                             | No       | Version-of-record PDF retained for hash-bound twelve-term aggregate extraction; supplementary questionnaires, assessment forms, demographics, and participant rows are excluded. |
