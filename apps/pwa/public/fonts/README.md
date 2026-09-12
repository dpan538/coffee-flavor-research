# Fraunces (owner's pick for the "words" half of the wordmark, 2026-09-12)

`Fraunces-Variable.woff2` / `Fraunces-Variable-Italic.woff2` (latin subset from Google Fonts, axes opsz / wght / SOFT / WONK) with
`OFL-Fraunces.txt` — SIL Open Font License 1.1, Undercase Type. Loaded in `src/style.css`; used by `.wordmark-serif`.

# MiSans (owner's download, subset on 2026-09-12)

`MiSans-Regular.woff2`, `MiSans-Medium.woff2`, `MiSans-Demibold.woff2` are subsets of the owner's MiSans download
(`~/Downloads/MiSans/woff2`), cut to the characters the app can show by `apps/pwa/scripts/subset-fonts.py` (re-run it after
adding copy). MiSans is free for commercial use under Xiaomi's MiSans licence; the owner keeps the licence text with the download.

# Self-hosted fonts

Drop the font files here; `src/style.css` declares the faces and falls back to system fonts until they exist.

| family | files expected | licence |
|---|---|---|
| MiSans (Xiaomi, Chinese + Latin) | `MiSans-Regular.woff2`, `MiSans-Medium.woff2`, `MiSans-Demibold.woff2` | free for commercial use per Xiaomi's MiSans licence (owner to keep a copy of the licence text here) |
| Stack Sans (display, en) | `StackSans-Regular.woff2`, `StackSans-Bold.woff2` | open licence per the owner (keep the licence text here) |

No font binary is committed until its licence text sits next to it.
