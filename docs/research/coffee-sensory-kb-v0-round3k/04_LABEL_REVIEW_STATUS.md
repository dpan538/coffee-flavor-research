# Label review status

## Governed workflow

The Round 3K schema separates raw professional expressions, deterministic
mapping rules, review queues, reviewer qualifications, final label decisions,
label targets, and training candidates. This prevents a normalized string or
model suggestion from silently becoming ground truth.

The nine controlled dispositions are retained independently:
`EXACT_CANONICAL_TARGET`, `MULTI_CANONICAL_TARGET`, `RANGE_LEVEL_TARGET`,
`SOURCE_LOCAL_TARGET`, `AMBIGUOUS_TARGET`, `CONTRADICTORY_TARGET`, `UNRESOLVED`,
`ABSTAIN`, and `OUTSIDE_ONTOLOGY`. Multi-target decisions retain multiple
targets; ambiguity and contradiction cannot be forced into one label.

## What can be deterministic

A final deterministic mapping is permitted only for an exact governed identity:
a WCR attribute identifier, governed SCA term, approved project lexicalization,
official scoresheet field, or explicit source-defined descriptor identity. The
mapping retains rule version, source snapshot, raw phrase, target, and decision
date. Normalization is limited to non-semantic operations such as Unicode, case,
whitespace, controlled punctuation, and source-declared identifier cleanup.

Metaphorical, qualified, multilingual, composite, source-local, multi-target,
ambiguous, or conflicting expressions require qualified human review. The
database contract supports two independent reviewers and adjudication, including
source-language qualification where applicable.

## Current status

No professional expression has been admitted and no expert review evidence was
supplied. Therefore every disposition metric is zero, every governed-expression
coverage rate is not evaluated, and `EXPERT_REVIEW_PERFORMED=false`.

The following 10,000-gate strata all remain at zero: 7,000 reviewed positive
records, 1,200 multi-target records, 1,000 abstention/unresolved records, and 500
ambiguous/conflicting records. The expression-level normalization targets also
remain unmet. No training-candidate label or manifest has been frozen.

Codex-authored candidates may be queued as `CANDIDATE` and
`NOT_TRAINING_LABEL`; they cannot satisfy qualified review requirements. A
future review phase must retain reviewer evidence rather than retrospectively
upgrading automated proposals.
