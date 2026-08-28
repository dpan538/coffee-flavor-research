# Negative tests

Round 3M includes executable failures for:

- blank scoresheets, rankings, and score-only rows yielding descriptors;
- judge rows creating coffee records;
- secondary tables double-crediting primary jury fields;
- unknown or pending rights entering model eligibility;
- public visibility creating affirmative rights;
- human/expert review states without real receipts;
- flavor text inferring roast or preparation;
- translations inflating source-native vocabulary;
- CoE editions inflating independent-family counts;
- NA values or an empty database passing gates;
- deprecated record-first gates authorizing training;
- cross-record or cross-mirror co-assertion pairs.

The complete SQL and adapter markers are included in the execution transcript.

The pre-hardening 13 named SQL negative checks were:

1. `human_state_without_receipt`;
2. `codex_cannot_create_human_receipt`;
3. `public_visibility_not_model_permission`;
4. `descriptor_route_index_must_match_source_artifact`;
5. `descriptor_hash_scope_must_match_source_artifact`;
6. `descriptor_nonstorage_reason_must_match_source_artifact`;
7. `secondary_layer_cannot_become_canonical_counting_assertion`;
8. `cross_record_coassertion_rejected`;
9. `not_applicable_model_rights_never_supports_eligibility`;
10. `stale_review_receipt_pointer_after_supersession`;
11. `superseded_receipt_excluded_from_human_universe`;
12. `superseded_receipt_validation`;
13. `assertion_cannot_restore_superseded_review_pointer`.

Each mutation raised its pinned SQLSTATE and named constraint. The final policy
group also passed `validation_contract`, `no_training_authority`, and
`saturation_false`. Adapter negatives additionally verified zero yield for
ranking, score-only, blank-form, and unauthoritatively filled WCC inputs.

The raw log contains 14 names under a `ROUND3M_NEGATIVE=` prefix because
`no_training_authority` is deliberately emitted inside the constraint-policy
group as well. It is not a fourteenth negative test path. The new superseded
pointer mutation raised SQLSTATE `23514` under
`round3m_descriptor_review_receipt_scope_ck`.

Restricted-capture negatives pin the governed root/manifest receipt and reject
manifest identity, capture hash, byte-size, URL-inventory, and timestamp drift.
A distinct secondary publication observation is permitted for preservation but
is rejected if changed to a canonical counting disposition.

Gate-artifact parity rejects identifier, required-value/type, universe,
pass/NA, blocker, or explanatory-note drift. Review-supersession regression
also proves that stale predecessor receipts cannot contribute to per-label or
multi-target gate metrics.

Migration 058 adds 32 named negatives, each asserting its expected constraint
or trigger. They reject hash-only claims; missing qualification, admission, or
row decision; reviewer/assertion/decision/protocol/scope/time mismatches;
expired or superseded authority; evidence reuse; automated actors presented as
humans; insufficient or non-final expert claims; unsupported self-adjudication;
ordinary update/delete; forked successors; multiple current leaves; old-path
gate credit; persisted synthetic evidence; and user approval treated as review.

```text
NEW_058_NEGATIVE_TEST_COUNT=32
OLD_SELF_ATTESTING_GATE_PATH_COUNT=0
PERSISTED_SYNTHETIC_HUMAN_FIXTURE_COUNT=0
```
