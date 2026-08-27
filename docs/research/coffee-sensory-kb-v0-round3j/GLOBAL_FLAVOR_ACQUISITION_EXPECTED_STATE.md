# Round 3J global flavor-acquisition expected state

This contract was frozen on 2026-08-27 before any new global source pilot or
full acquisition following continuation checkpoint
`0328c5bc83a20018b1be848d7e560baaf59a77ac`. The machine-readable contract is
`db/data/round3j/global_flavor_acquisition_expected_state.tsv`.

## Scope decision

Round 3J now maximizes lawful, provenance-complete, source-authored coffee
flavor descriptions and related sensory observations across source classes A
through I. Language and geography remain required metadata. They are not
quotas and do not block broad acquisition.

```ini
ROUND3J_REGIONAL_AUDIT_COMPLETE=true
ROUND3J_REGIONAL_DATA_ACQUISITION_COMPLETE=false
REGIONAL_SOURCE_FRAME_BLOCKS_GLOBAL_ACQUISITION=false
REGIONAL_REPRESENTATIVENESS_CLAIM=false
REGIONAL_MINIMUM_QUOTA_ENFORCED=false
REGIONAL_ACQUISITION_BLOCKING_GATE=false
GLOBAL_FLAVOR_ACQUISITION_COMPLETE=false
```

The completed regional candidate-frame audit remains useful for future
source-held-out evaluation, bias analysis, soft reweighting, targeted
augmentation, and extreme-skew detection. It is not an acquisition-completion
claim.

## Frozen baseline and scale targets

| Metric                                        |         Baseline |                     Minimum | Preferred |
| --------------------------------------------- | ---------------: | --------------------------: | --------: |
| Governed unique normalized expressions        |            2,996 |                       6,000 |    10,000 |
| Contemporary tasting-language source families |                3 | 12 admitted flavor families |        20 |
| Admitted flavor documents                     |            3,289 |                      10,000 |    25,000 |
| Admitted expression occurrences               | not materialized |                      40,000 |   100,000 |
| Training-eligible unique expressions          |      not audited |                       5,000 |     8,000 |
| Source-local sensory samples/configurations   |              230 |                         500 |     1,000 |
| Coffee-sensory source families                |                9 |                          12 |        15 |
| Source classes with admitted data             |      not audited |                           6 |         8 |

The thresholds are acquisition and engineering entry gates, not scientific
sufficiency claims. They may not be lowered after acquisition begins merely to
produce a passing result. Raw source rows, admitted documents, unique
identities, occurrences, and task-specific effective units must always be
reported separately.

## Exit contract

`ROUND3J_GLOBAL_FLAVOR_CORPUS_READY` requires the minimum global acquisition
target plus lexical readiness, association or context readiness, a held-out
source split, label-provenance rate `1.0000`, acceptable source concentration,
and deterministic reproduction. Question and adaptive-policy readiness remain
false. No model, embedding baseline, ranking model, or adaptive policy may be
trained in Round 3J.

## Immutability receipt

The original acquisition and regional artifacts remain unchanged:

| Artifact                                   | SHA-256                                                            |
| ------------------------------------------ | ------------------------------------------------------------------ |
| `source_candidate_register.tsv`            | `3cbc8890a4e3c1fd65b1c664794ce5fe5f986d4f889b835e07e3d6a71d3c2471` |
| `acquisition_outcome_ledger.tsv`           | `a57aee1a59a33efe5a1110ece439e89a30be90e60f1c6583d646b6c80ef8f918` |
| `acquisition_batch_ledger.tsv`             | `10d60dc5727e48e3ff9291c065428dd19d3dc72734b06c5fa28a13f3ac7c2692` |
| `regional_source_candidate_register.tsv`   | `4867cb403a8266b1ea66d46fa3b9900c0ab8ffddd8df9c84a70e4dc7035b3621` |
| `regional_permission_request_dossiers.tsv` | `1ed79e23fd00e75b1d474cca2e2e94a8f9db3fb6e6df3f5989fe927341b99b0f` |
| `regional_stop_rule_decision.tsv`          | `5f7f343ac151d072ee104a25176b2e9e17492bfec078e6bb876fca6d750d5117` |

The original Condition-B result remains valid within the original 17-candidate
frame. Only its global effect is superseded.
