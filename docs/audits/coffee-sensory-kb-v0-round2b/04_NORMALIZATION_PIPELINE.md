# Round 2B normalization pipeline

Date: 2026-08-24

Pipeline: `normalization.en_v1`

Version: `1`

## Contract

The pipeline preserves phrase boundaries and normalizes orthography
conservatively. It does not stem, infer ontology type, infer missing language,
or promote an observed expression to a canonical concept. Industry expressions
remain language observations.

The frozen rules hash is
`b32e4aec8b6ceacd067c5dd920996d4d71603647b49bbc910cd7ebcc32922824`;
the generator hash is
`580e367e0b14ab6f84e00daee0f51da3eaa61275ec9c017be1f3efed6f52b5eb`;
and the recorded code commit is
`d90b0bd3ee52b449fa1cebf7fca64e6f05ce8aa0`. The full contract is captured in
the [generation receipt](../../../db/data/round2b/generation_receipt.json) and
implemented by the
[pilot generator](../../../db/scripts/generate-round2b-pilot.py).

## Ordered pipeline

1. Read the pinned Firstbloom tasting-note field only from the separately
   obtained source checkout; do not emit the complete field.
2. Split on comma, semicolon, vertical bar, CR, LF, and Unicode bullet
   characters. Slash and the word “and” are not delimiters.
3. Record each fragment's SHA-256, Unicode character count, and zero-based
   half-open code-point offsets into the hashed source field.
4. Make every surface equal to any complete selected source field hash-only
   globally. Make fragments longer than 80 Unicode characters hash-only.
5. Submit remaining unique hashes to two independent Codex-assisted
   project-curation passes. Retain `en` only when both passes classify the hash
   as `ENGLISH_TASTING_LANGUAGE`.
6. Apply `structural-prose-gate-v2`, rejecting Unicode control/format
   characters, sentence punctuation, personal-pronoun or finite-auxiliary
   tokens, repeated connective tokens, and phrases longer than eight Unicode
   word tokens, in that order.
7. Apply Unicode NFC, conservative punctuation translation, Unicode lowercase
   under the recorded PostgreSQL cluster collation, Unicode-whitespace collapse,
   and trim.
8. Apply the ordered exact whole-phrase variants below. Do not replace
   substrings and do not stem.

| Order | Exact input     | Exact output    |
| ----: | --------------- | --------------- |
|    10 | `earl gray`     | `earl grey`     |
|    20 | `earl gray tea` | `earl grey tea` |
|    30 | `black currant` | `blackcurrant`  |

Punctuation normalization maps curly apostrophes to ASCII apostrophe, curly
quotes to ASCII double quote, Unicode dash variants to hyphen-minus, and the
Unicode ellipsis to three ASCII periods. The structural gate runs before these
normalizations so sentence-like input cannot be made less visible by a later
rewrite.

## Admission review

The public
[hash-only admission ledger](../../../db/data/round2b/expression_admission_review.tsv)
contains 2,766 unique candidate hashes and no reviewed phrase text. The
[review metadata](../../../db/data/round2b/expression_admission_review.json)
records both independent passes.

| Review measure                                        |        Value |
| ----------------------------------------------------- | -----------: |
| Reviewed unique hashes                                |        2,766 |
| Agreement                                             |        2,597 |
| Disagreement                                          |          169 |
| Raw agreement                                         | 0.9389009400 |
| Cohen's kappa                                         | 0.6678138580 |
| Consensus English tasting language                    |        2,411 |
| Consensus narrative/non-descriptor                    |           75 |
| Consensus non-English                                 |          103 |
| Consensus uncertain                                   |            8 |
| Final admitted English surfaces after structural gate |        2,124 |
| Hash-only review-consensus surfaces                   |          355 |
| Hash-only structural-gate surfaces                    |          287 |

These were two Codex-assisted non-human curation passes. They are neither two
human reviewers nor an automated language detector. Agreement describes the
admission decisions only; it does not validate sensory truth or canonical
mapping.

An initial spot audit found two accepted structural leaks. Both were removed by
`structural-prose-gate-v2`. Two independent final spot-audit ledgers reviewed
the same deterministic 271-row packet and each reported zero accepted blockers.
The public metadata records the failed audit and remediation rather than hiding
it.

## Retention outcome

The frozen snapshot contains 6,818 fragment occurrences: 5,564 admitted short
surfaces and 1,254 hash-only observations. No admitted observation hash equals
a complete selected source-field hash. All admitted lexical expressions carry
`en`; non-English and uncertain candidates remain hash-only, and no alternative
language tag is guessed.

The observation inventory hash is
`792ed3e77f7975c92b6feb8de0124cc047245c2d2640280913a8a94ef16e18c7`;
the normalized output inventory hash is
`301c45168413d1cf281f7c5a927bbc0e8ce57910dc68bf0cb07ec5ef8a845d76`.
Database constraints keep hash-only observations from acquiring surface text
and keep retained observations tied to the frozen pipeline.
