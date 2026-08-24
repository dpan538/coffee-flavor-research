# Round 2B known gaps

Date: 2026-08-24

These limitations are properties of the frozen pilot, not hidden completion
claims.

## Source and time coverage

- The corpus has one acquired licensed source: the historical Firstbloom
  secondary aggregation. Its 215 publisher identities do not equal 215
  independently reviewed or licensed sources.
- Source listing dates span 2017-12-29 through 2021-01-13. The pilot says
  nothing about current offerings or language change after that period.
- No live roaster site was scraped. Of 15 policy reviews, eight were blocked,
  three were unknown and treated as blocked, and three were manual-only. This
  leaves no lawful multi-source comparison in the frozen snapshot.
- A dataset-level CC BY 4.0 grant does not independently prove authorization by
  every upstream roaster. The project mitigates this by retaining only governed
  short derived phrases, metadata, and hashes, but it cannot erase that
  secondary-source limitation.

## Representativeness

- The deterministic frame balances releases across available Firstbloom
  publishers, not countries, contemporary markets, publisher sizes, or process
  strata.
- Roaster country and publisher size are absent and were not inferred from
  domains or time zones. Country prevalence for expressions is therefore
  `NULL`.
- The 36 origin values are Firstbloom source codes for coffee origin, not
  validated roaster locations or asserted ISO identifiers.
- English is the only admitted language. Non-English candidates remain
  hash-only without a guessed language tag; Simplified Chinese population is
  outside this pilot.

## Raw evidence and reproducibility

- Complete tasting-note strings, long descriptions, rejected review phrases,
  and consumer reviews are deliberately absent. Document `raw_text` is `NULL`.
- A public rebuild requires separately obtaining the pinned Firstbloom commit
  `a6cb0026d1af9642724793c799bbc48dc189ba35`. The repository alone is therefore
  not a complete raw-data reproduction, and the snapshot correctly records
  `raw_public_reproducibility_complete=false`.
- Source hashes and fragment offsets make a separately obtained input
  verifiable, but they cannot reveal or reconstruct excluded text.
- Product URLs and roast dates were not available in the selected source rows
  and remain `NULL`; missing values were not inferred.

## Admission review

- The two expression-admission passes were Codex-assisted project curation, not
  human reviews and not automated language detection. Raw agreement
  (`0.9389009400`) and Cohen's kappa (`0.6678138580`) measure only four-way
  admission decisions.
- Conservative false negatives are accepted to reduce narrative or non-English
  leakage. Hash-only exclusions therefore include potentially useful phrases
  that would need a newly rights-reviewed, human-governed pass before reuse.
- A first structural spot audit failed on two accepted fragments. The failure
  is preserved in the public metadata; `structural-prose-gate-v2` removed both,
  and two final 271-row spot audits found zero accepted blockers. This does not
  turn the remaining phrases into sensory ground truth.

## Statistical limits

- The vocabulary is not converged: 48 new normalized expressions appeared in
  batch 16, and 74.022183% of normalized expressions are hapaxes.
- Final fixed-seed bootstrap top-five-neighbour mean Jaccard is only
  `0.3686790531`, despite strong consecutive-batch rank overlap. Co-occurrence
  neighbourhoods are not stable enough to support perceptual claims.
- NPMI is sensitive to rare events; a singleton pair can score `1.0`. All 4,600
  pairs remain empirical language measurements and never become canonical
  sensory-neighbour edges automatically.
- The strict exact-expression projection resolves 1,866 of 5,564 occurrences
  and 57 of 1,713 normalized identities; 3,698 occurrences and 1,656 identities
  remain unresolved. Seven occurrences resolve to active composite references
  and none to an active qualifier. These deliberately narrow counts are not a
  surface-guessed corpus-wide type distribution.

## Product and history limits

- There are 2,474 release documents for 2,383 product identities. The 129
  duplicate-review rows preserve 96 publisher/product-key candidates and 33
  content-hash candidates without overwriting historical observations.
- This duplicate policy preserves source history, but source identifiers and
  hashes cannot establish that two differently identified listings represent
  the same physical coffee lot.

## Epistemic boundary

No frequency, modifier context, duplicate judgment, process label, retrieval
candidate, or co-occurrence measurement in Round 2B is evidence that a coffee
objectively tastes like a concept. Industry language informs normalization and
retrieval evaluation only. Ontology extension requires a separate,
source-versioned curation decision and is never automatic.

## Retrieval-review limits

- The 300-case mapping audit was reviewed by two independent Codex-assisted
  project passes and a distinct Codex-assisted adjudication pass. No reviewer
  was human, so the resulting grades are an engineering audit baseline rather
  than human sensory-panel evidence.
- Held-out cases were frozen before the review and were not tuning-eligible,
  but all three judgments were produced in one model family. Agreement cannot
  establish external validity or eliminate shared-model bias.
- The deterministic baseline uses approved lexicalizations, `pg_trgm`, and a
  one-hop typed graph only. No embedding or `pgvector` baseline was run.

The frozen evidence for these gaps is the
[rights matrix](../../../db/data/round2b/source_rights.tsv),
[source manifest](../../../db/data/round2b/firstbloom_source_manifest.json),
[generation receipt](../../../db/data/round2b/generation_receipt.json), and
[staged diagnostics](../../../db/data/round2b/pilot_diagnostics.json).
