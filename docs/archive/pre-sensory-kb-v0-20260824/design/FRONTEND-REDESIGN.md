# Frontend Redesign

## Repositioning

The site moved from an Astro research MVP toward a React-based experimental digital publication: high-contrast editorial grid, sensory specimen index, node field, and visual poem.

It is no longer designed as a dashboard, SaaS page, card knowledge base, ecommerce page, cafe menu, or method landing page.

## Visual System

- Light field: warm gray paper, near-black type, pale grid lines, acid green accent.
- Dark field: near-black background, warm white nodes, glow, low-opacity structure lines.
- Layout: 12-column desktop grid, 4-column mobile grid, thin dividers, edge notes, indices, coordinates, metadata.
- Typography: Bodoni Moda for Latin display, Noto Serif SC as CJK display fallback, IBM Plex Sans plus Noto Sans SC for body, IBM Plex Mono for metadata.
- Category difference is expressed through position, density, labels, and shape before saturated category colors.

## Page Direction

- Home begins with the descriptor field, not a hero pitch.
- Atlas defaults to FIELD and offers INDEX and MAP.
- Detail pages are single descriptor specimens.
- Methodology begins with method index, version, data status, six dimensions, and source levels.

## Motion System

Anime.js is the only main animation library. Cursor motion is enabled only for fine pointer and hover-capable devices. Reduced motion disables follower inertia and route/text motion while preserving all content and controls.

Scroll scenes expose progress without hijacking scroll. The current scroll reveal is intentionally conservative to avoid route-exit observer leaks.

## Remaining Visual Risks

- The six Game-icons candidates are a spike, not the final descriptor image language.
- The CJK font payload is large because Fontsource slices many subsets; future font subsetting would improve build size.
- The comparison overlay is intentionally functional and restrained; the next pass should make split-screen relation graphics more expressive.
