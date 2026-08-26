# Round 3J regional stop-rule decision

The machine-readable decision record is
`db/data/round3j/regional_stop_rule_decision.tsv`.

## Problem

The original 17-candidate acquisition frame did not explicitly cover the
project's target user markets. Its four batches and Condition-B result cannot
justify global acquisition closure.

## Decision

Preserve the original no-gain audit and its exact evidence. Supersede only its
global stop implication, then audit separate language, preference, sensory,
industry, and community-permission lanes for Mainland China, Taiwan, Australia
/ New Zealand, United States / Canada, Japan, and South Korea.

```ini
ORIGINAL_STOP_RULE_VALID_WITHIN_ORIGINAL_FRAME=true
ORIGINAL_STOP_RULE_PRESERVED=true
ORIGINAL_STOP_RULE_GLOBAL_EFFECT_SUPERSEDED=true
ORIGINAL_STOP_RULE_SUPERSEDED_BY_REGIONAL_SCOPE_EXTENSION=true
REGIONAL_SOURCE_FRAME_COMPLETE=false
GLOBAL_ACQUISITION_COMPLETE=false
```

This is a scope extension, not a correction to the original audit. The original
candidate register, outcome ledger, four acquisition batches, observed gains,
three consecutive no-material-gain count, and Condition-B conclusion retain
their original meanings within their original frame.

## Regional lane rule

Each region begins with its own counter. If its declared thresholds are not
met, that lane may stop only after two consecutive targeted no-material-gain
batches for that same region. Every counted batch must include both:

1. a structured dataset or research search; and
2. a community or user-generated-content permission search.

No-gain results from another region, from a global search, or from only one of
those two search classes do not advance the counter. Meeting a candidate-count
threshold closes the source-frame audit only when independence and rights/access
completeness also pass.

Both required search lanes must have recorded scope and evidence paths. A
material-gain batch or an intervening batch missing either lane resets that
region's consecutive counter to zero. Batch deltas are preserved in the
separate regional outcome ledger rather than reconstructed from a later mutable
register state.

## Global rule

The global stop rule is disabled until:

```ini
ALL_CORE_REGIONAL_SOURCE_FRAMES_COMPLETE=true
ALL_SECONDARY_REGIONAL_SOURCE_FRAMES_AUDITED=true
```

Those conditions are prerequisites, not a sufficient declaration of global
acquisition completion. Round 3J remains open after the regional audit unless
all other applicable acquisition and training-corpus conditions are also
resolved.

## Contact and acquisition boundary

Metadata and rights evidence may be audited. Contact packages may be drafted.
No request may be sent and no permission-controlled community content may be
collected without explicit user authorization. Public visibility is not reuse,
privacy, public-release, or model-use permission.

## Pre-acquisition validation

- Original candidate-frame count: `17`.
- Original source register SHA-256:
  `3cbc8890a4e3c1fd65b1c664794ce5fe5f986d4f889b835e07e3d6a71d3c2471`.
- Original outcome ledger SHA-256:
  `a57aee1a59a33efe5a1110ece439e89a30be90e60f1c6583d646b6c80ef8f918`.
- Original batch ledger SHA-256:
  `10d60dc5727e48e3ff9291c065428dd19d3dc72734b06c5fa28a13f3ac7c2692`.
- Regional source-candidate register: schema only, zero candidates.
- Regional acquisition batch ledger: schema only, zero batches.
- Regional expected state committed before regional acquisition.
