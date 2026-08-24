# 03 — Constraint Tests

- Receipt date: 2026-08-24
- Server: PostgreSQL 17.11
- Suite: `db/tests/negative.sql`

The negative suite runs inside an outer transaction and rolls it back. Each
case executes the prohibited write in a nested block, captures PostgreSQL's
actual `RETURNED_SQLSTATE` and `CONSTRAINT_NAME`, and fails the suite if either
diagnostic differs from the contract.

## Recorded failure matrix

| prohibited operation                             | SQLSTATE | recorded constraint                               | result |
| ------------------------------------------------ | -------- | ------------------------------------------------- | ------ |
| Duplicate `sensory.grapefruit` concept key       | `23505`  | `concept_key_uq`                                  | PASS   |
| Grapefruit self `sensory_neighbour` edge         | `23514`  | `concept_relation_self_allowed_ck`                | PASS   |
| Reverse duplicate of a symmetric pair            | `23505`  | `concept_relation_type_endpoints_uq`              | PASS   |
| Direct `broader_than` cycle                      | `23514`  | `concept_relation_hierarchy_cycle_ck`             | PASS   |
| Indirect three-node `broader_than` cycle         | `23514`  | `concept_relation_hierarchy_cycle_ck`             | PASS   |
| Active external relation without support         | `23514`  | `concept_relation_active_source_support_ck`       | PASS   |
| Active external lexicalization without support   | `23514`  | `lexicalization_active_source_support_ck`         | PASS   |
| Promotion with zero targets                      | `23514`  | `promotion_event_exactly_one_target_ck`           | PASS   |
| Promotion with two targets                       | `23514`  | `promotion_event_exactly_one_target_ck`           | PASS   |
| Promotion backed by a rejecting review           | `23514`  | `promotion_event_review_permits_ck`               | PASS   |
| Promotion targeting a candidate concept          | `23514`  | `promotion_event_target_active_ck`                | PASS   |
| Reference calibration below its declared scale   | `23514`  | `reference_calibration_scale_bounds_ck`           | PASS   |
| Non-terminal model run with `completed_at`       | `23514`  | `model_run_terminal_timestamp_ck`                 | PASS   |
| Resolved inference with no candidate             | `23514`  | `mapping_inference_resolved_candidate_count_ck`   | PASS   |
| Explicitly unresolved inference with a candidate | `23514`  | `mapping_inference_unresolved_candidate_count_ck` | PASS   |

## Enforcement notes

- Symmetric endpoints are canonicalized before the ordinary endpoint unique
  key runs, so `A–B` and `B–A` cannot coexist.
- Hierarchical writes take a transaction advisory lock and use recursive graph
  reachability. Both direct and indirect cycle attempts were rejected.
- Source-support checks are deferrable constraint triggers. The tests force
  them to `IMMEDIATE` to prove final-transaction enforcement, then restore
  deferred mode.
- Reciprocal support triggers recheck assertion IDs after support insert,
  delete, or retarget operations.
- Scale-bound triggers read the selected scale; a used-scale guard prevents
  later changes to bounds or value semantics.
- Pending inference workflows may carry candidates. Only `resolved` requires
  one or more, and explicit `unresolved` requires zero.
- Promotion validation records governance history but never changes or creates
  the canonical target.

The same suite passed during both from-zero rebuilds. No rejected fixture row
survived its transaction.

```text
NEGATIVE_CASE_COUNT=15
NEGATIVE_TEST_PASS=true
```
