# Round 3G evidence artifacts

This directory contains the expected-state contract, named-source register,
source-family/file inventories, de-identified source-derived RATA summary,
exact Wiktionary revision metadata, evidence matrix and review decisions.

`Dataset.xlsx` is not committed. Its Mendeley v1 SHA-256 was independently
verified as `299c4ee083b8cc5a67608c1280a75e963e93d64478d2d70755ad299f9e5e8dda`.
It contains pseudonymous panelist initials, so its public-export decision is
`EXTERNAL_ONLY`. `liberica_rata_summary_matrix.tsv` transcribes only the ten
published RATA summary rows at `RATA Test!A158:J168`; it contains no panelist
identifier or row-level response.

The two Wiktionary JSON files contain page title, missing-title status, page ID,
revision ID, parent ID and timestamp metadata returned by the Action API on
2026-08-25. They contain no entry definitions or quotation corpus.

Run `python3 db/scripts/test-round3g-artifact-contract.py` to verify record
counts, local hashes, file sizes, expected-state sections and evidence-direction
counts without network access.
