# Coffee Flavor Atlas

> A research-driven visual language system for coffee descriptors, built on
> formal sensory frameworks, open data where reuse is permitted, and explicitly
> labeled uncertainty everywhere else.

Coffee Flavor Atlas / 咖啡风味图谱 is an experimental research prototype and
digital publication about coffee flavor language. It combines bilingual
descriptor records, sensory association profiles, provenance notes, and
expressive web interaction without presenting itself as a sensory standard or a
coffee scoring authority.

- Experimental research prototype
- 24 pilot descriptors
- English / Simplified Chinese
- Project-curated sensory association profiles
- No claim of universal sensory measurement

## 1. Overview

Coffee Flavor Atlas is a vocabulary and interface prototype. It explores how a
small set of coffee flavor descriptors can be structured, searched, visualized,
and compared while keeping uncertainty visible.

The project is not a coffee shop, ecommerce catalog, coffee sample database,
formal cupping platform, or replacement for professional sensory evaluation.

## 2. 中文简介

咖啡风味图谱是一个研究型前端原型，关注咖啡风味描述词如何被双语组织、
检索、可视化和比较。当前 24 个词条及其分数均为项目整理的试验性
sensory association profile，不是化学检测值，也不是任何具体咖啡样本的
固定杯测结果。

## 3. Project Status

Current status: public baseline for an experimental MVP.

The app includes the first 24 descriptors, a static React Router + Vite
frontend, schema-validated data, Atlas exploration, sensory map, descriptor
detail pages, comparison tools, methodology notes, and smoke tests.

No formal release, DOI, external deployment, or peer-reviewed publication has
been created yet.

## 4. Why This Project Exists

Coffee flavor language is useful because it points to shared sensory patterns.
It is also subjective because descriptors depend on culture, translation,
training, context, and the coffee being observed.

This project tests whether an interface can make those boundaries clearer:
descriptor records are structured, provenance is visible, and draft sensory
profiles are shown as ranges instead of fixed facts.

## 5. Current Scope

- 24 pilot descriptors across floral, fruit, sweet, nut/cocoa, roasted, green,
  fermented, and unresolved categories.
- English and Simplified Chinese labels, aliases, and short summaries.
- Six sensory association dimensions for each descriptor.
- Search, category filtering, spatial field, index view, map view, comparison,
  detail pages, and methodology page.
- Six external SVG candidates used as an asset spike, with attribution
  documented.

## 6. Features

- Bilingual descriptor search, including aliases.
- Category filters and URL-restorable Atlas state.
- FIELD, INDEX, and MAP Atlas views.
- SVG sensory map using sweetness and sourness associations.
- Two-descriptor comparison with computed shared traits and largest
  differences.
- Static detail page for every descriptor.
- Reduced-motion support and keyboard-accessible navigation.
- Build-time Zod validation for categories, sources, and descriptors.

## 7. Research Model

The data model separates:

- descriptor identity and bilingual labels;
- category and descriptor status;
- sensory modalities;
- sensory association ranges;
- confidence and evidence status;
- source registry entries;
- editorial notes for uncertain or boundary terms.

All descriptor records are validated in `packages/flavor-data/src/schema.ts`.

## 8. Descriptor vs Coffee Observation

A descriptor is a language node such as `lemon` or `dark-chocolate`.

A coffee observation would be a record that a specific coffee, brewed in a
specific way, was perceived by a specific person or panel at a specific time.

This repository currently models descriptors, not coffee observations.

## 9. Sensory Association Profiles

The six range dimensions are sourness, sweetness, bitterness, aroma prominence,
body, and roast/fermentation association.

Each value is a range with `min`, `typical`, and `max` on a 0 to 5 scale. These
ranges are project-curated drafts for interface testing. They are not chemical
measurements, universal sensory scores, official SCA or WCR values, or fixed
results for any coffee.

## 10. Data Provenance

The source registry lives in `packages/flavor-data/src/sources.ts`.

The current registry distinguishes:

- reference frameworks used for background orientation only;
- open datasets that may support future validation if their reuse terms allow;
- project-created editorial pilot data.

External public availability does not automatically mean the material may be
redistributed or reused without limits.

## 11. Research Limitations

- The current 24 profiles are project-curated drafts.
- Chinese labels, aliases, and category boundaries require bilingual sensory
  review.
- The Atlas does not reproduce the SCA Coffee Taster's Flavor Wheel design,
  protected graphics, complete vocabulary, definitions, or proprietary forms.
- The app does not republish WCR, SCA, Cup of Excellence, or commercial source
  materials as a dataset.
- Open datasets listed in the registry are not used to compute the current
  scores.
- Boundary terms such as `cheese`, `winey`, and `bellflower` remain explicitly
  marked as uncertain or context-sensitive.

## 12. Tech Stack

- React Router Framework Mode with `ssr: false`
- Vite
- React
- TypeScript strict mode
- Anime.js
- Zod
- Vitest
- Playwright
- Native CSS with custom properties
- npm and `package-lock.json`

## 13. Getting Started

```bash
npm ci
npm run dev
```

Open the local development URL printed by React Router.

For a production-like static preview:

```bash
npm run build
npm run preview
```

## 14. Available Scripts

- `npm run dev`: start the React Router development server.
- `npm run build`: generate the static production build.
- `npm run preview`: preview `build/client` with Vite.
- `npm run check`: generate route types and run TypeScript.
- `npm run test`: run Vitest tests.
- `npm run test:smoke`: run Playwright smoke tests.
- `npm run format`: format the repository with Prettier.
- `npm run format:check`: check formatting without writing files.

React Router 8 currently warns that Node `>=22.22.0` is preferred. Local checks
have passed on Node `22.21.0`, but CI uses a current Node 22 runtime. Playwright
uses the local Chrome channel outside CI and bundled Chromium inside CI.

## 15. Repository Structure

```text
app/                         React Router app, routes, components, motion, CSS
packages/flavor-data/src/    Descriptor data, categories, sources, schema, tools
public/vendor/game-icons/    Six documented SVG candidates for asset research
tests/                       Vitest and Playwright tests
docs/                        Methodology, decisions, architecture, license scope
LICENSES/                    Non-code license texts
```

## 16. Adding or Editing a Descriptor

1. Edit `packages/flavor-data/src/descriptors.ts`.
2. Use an existing category from `packages/flavor-data/src/categories.ts`.
3. Keep labels, aliases, summaries, modalities, source IDs, and all six sensory
   ranges complete.
4. Keep every score in the 0 to 5 range with `min <= typical <= max`.
5. Add or update an editorial note for boundary, compound, unresolved, broad,
   culturally sensitive, or translation-sensitive terms.
6. Document the source or provenance for any substantive change.
7. Run `npm run check`, `npm run test`, and `npm run build`.

Score changes must not describe the project-curated profiles as scientific
settled facts.

## 17. Citation

`CITATION.cff` is the authoritative citation metadata for this repository.

Use GitHub's "Cite this repository" feature when available. Cite a specific
release once one exists. Until then, cite the exact commit SHA used.

Example format:

```text
dpan538. (2026). Coffee Flavor Atlas [Computer software].
GitHub. https://github.com/dpan538/coffee-flavor-research.
Commit <commit-sha>.
```

BibTeX fallback:

```bibtex
@software{coffee_flavor_atlas_2026,
  author = {dpan538},
  title = {Coffee Flavor Atlas},
  year = {2026},
  url = {https://github.com/dpan538/coffee-flavor-research},
  note = {Experimental research prototype; cite the exact release or commit used}
}
```

The first formal release should add a version, `date-released`, and DOI only
after those resources actually exist.

## 18. Licensing

This repository uses layered licensing.

- Application source code is licensed under the MIT License: [LICENSE](LICENSE).
- Project-authored research prose and curated descriptor content are licensed
  under CC BY 4.0: [LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt).
- Detailed scope rules are in
  [docs/LICENSE-SCOPE.md](docs/LICENSE-SCOPE.md).
- Third-party materials are not automatically re-licensed by this project:
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and
  [docs/ASSET-LICENSES.md](docs/ASSET-LICENSES.md).

## 19. Third-Party Materials

Game-icons SVG candidates, Fontsource webfont packages, npm dependencies, and
any referenced external frameworks or datasets retain their own licenses and
attribution requirements.

The current public baseline includes six Game-icons.net SVG candidates under
CC BY 3.0. Attribution details are documented before use.

## 20. Contributing

Small, well-documented contributions are welcome. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) before proposing data, translation, visual,
or code changes.

Do not submit scraped commercial data, unclear images or SVGs, protected flavor
wheel graphics, or score changes without provenance.

## 21. Roadmap

- Review the 24 descriptor records with bilingual coffee sensory practitioners.
- Replace or confirm the six SVG candidate assets before expanding the visual
  system to all descriptors.
- Add a documented validation workflow for future score revisions.
- Prepare a first tagged release only after asset, citation, and data review.

## 22. Acknowledgements

This project is informed by public discussion around coffee sensory language,
formal reference frameworks, open data practices, bilingual terminology work,
and digital editorial design. Reference frameworks and datasets are treated as
background or future validation material unless their reuse terms clearly allow
more.
